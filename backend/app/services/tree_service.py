"""树木档案业务逻辑。"""

from sqlalchemy import func, or_

from ..constants import ENUM_GROUPS
from ..errors import ValidationError
from ..extensions import db
from ..models import GreenSpace, TreeMaintenance, TreeProfile
from ..utils.dates import format_date
from ..utils.numbers import to_float
from ..utils.sorting import parse_sort
from .base_service import BaseService
from .code_generator import year_prefix


class TreeService(BaseService):
    """树木档案：一树一档，支持按保护级别与行政区检索。"""

    model = TreeProfile
    label = "树木档案"
    code_field = "tree_no"
    code_width = 4

    SORTABLE = {
        "tree_no": TreeProfile.tree_no,
        "tree_species": TreeProfile.tree_species,
        "dbh_cm": TreeProfile.dbh_cm,
        "height_m": TreeProfile.height_m,
        "age_years": TreeProfile.age_years,
        "register_date": TreeProfile.register_date,
        "created_at": TreeProfile.created_at,
    }

    @classmethod
    def code_prefix(cls):
        return year_prefix("TR")

    # ------------------------------------------------------------ 校验
    @classmethod
    def prepare_instance(cls, instance, payload):
        green_space_id = payload.get("green_space_id", instance.green_space_id)
        space = db.session.get(GreenSpace, green_space_id) if green_space_id else None
        if space is None:
            raise ValidationError("建档失败", details={"green_space_id": "所选绿地不存在"})

        longitude = payload.get("longitude", instance.longitude)
        latitude = payload.get("latitude", instance.latitude)
        if (longitude is None) != (latitude is None):
            raise ValidationError(
                "建档失败", details={"longitude": "经纬度需同时填写，或同时留空（仅用文字描述点位）"}
            )

        planted_date = payload.get("planted_date", instance.planted_date)
        register_date = payload.get("register_date", instance.register_date)
        if planted_date and register_date and planted_date > register_date:
            raise ValidationError(
                "建档失败", details={"planted_date": "栽植日期不能晚于建档日期"}
            )

    # ------------------------------------------------------------ 查询
    @classmethod
    def _apply_filters(cls, query, filters):
        if filters.get("green_space_id"):
            query = query.filter(TreeProfile.green_space_id == filters["green_space_id"])
        if filters.get("protection_level"):
            query = query.filter(TreeProfile.protection_level == filters["protection_level"])
        if filters.get("vigor"):
            query = query.filter(TreeProfile.vigor == filters["vigor"])
        if filters.get("district"):
            query = query.join(GreenSpace).filter(GreenSpace.district == filters["district"])
        keyword = filters.get("keyword")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    TreeProfile.tree_no.like(like),
                    TreeProfile.tree_species.like(like),
                    TreeProfile.scientific_name.like(like),
                    TreeProfile.responsible_unit.like(like),
                    TreeProfile.responsible_person.like(like),
                    TreeProfile.location_desc.like(like),
                )
            )
        return query

    @classmethod
    def list_trees(cls, filters, args):
        """列表查询：用相关子查询带出每株树的养护措施次数与最近措施日期。"""

        maintenance_count = (
            db.select(func.count(TreeMaintenance.id))
            .where(TreeMaintenance.tree_id == TreeProfile.id)
            .correlate(TreeProfile)
            .scalar_subquery()
        )
        last_care_date = (
            db.select(func.max(TreeMaintenance.care_date))
            .where(TreeMaintenance.tree_id == TreeProfile.id)
            .correlate(TreeProfile)
            .scalar_subquery()
        )

        query = (
            cls._apply_filters(
                db.session.query(TreeProfile, maintenance_count, last_care_date),
                filters,
            )
            .order_by(parse_sort(args, cls.SORTABLE, TreeProfile.tree_no.asc()))
        )
        return query

    @classmethod
    def serialize_row(cls, row):
        tree, maintenance_count, last_care_date = row
        data = tree.to_dict()
        data["maintenance_count"] = maintenance_count or 0
        data["last_care_date"] = format_date(last_care_date)
        return data

    @classmethod
    def filtered_summary(cls, filters):
        """当前筛选条件下的株数，及按保护级别的分布。"""

        total = cls._apply_filters(db.session.query(func.count(TreeProfile.id)), filters).scalar() or 0
        rows = (
            cls._apply_filters(
                db.session.query(TreeProfile.protection_level, func.count(TreeProfile.id)),
                filters,
            )
            .group_by(TreeProfile.protection_level)
            .all()
        )
        levels = {code: 0 for code in ENUM_GROUPS["tree_protection_level"].values}
        for level, count in rows:
            levels[level] = count
        return {"total": total, "protection_level_summary": levels}

    @classmethod
    def detail(cls, obj_id):
        """树木档案：基础信息 + 全部养护措施 + 措施统计。"""

        tree = cls.get(obj_id)
        total, total_cost, last_date = (
            db.session.query(
                func.count(TreeMaintenance.id),
                func.coalesce(func.sum(TreeMaintenance.cost), 0),
                func.max(TreeMaintenance.care_date),
            )
            .filter(TreeMaintenance.tree_id == tree.id)
            .one()
        )
        type_rows = (
            db.session.query(TreeMaintenance.care_type, func.count(TreeMaintenance.id))
            .filter(TreeMaintenance.tree_id == tree.id)
            .group_by(TreeMaintenance.care_type)
            .all()
        )
        care_summary = [
            {
                "care_type": care_type,
                "care_type_label": ENUM_GROUPS["tree_care_type"].label(care_type),
                "count": count,
            }
            for care_type, count in type_rows
        ]
        return {
            "tree": tree.to_dict(detail=True),
            "statistics": {
                "maintenance_count": total or 0,
                "total_cost": to_float(total_cost) or 0,
                "last_care_date": format_date(last_date),
            },
            "care_summary": care_summary,
        }


class TreeMaintenanceService(BaseService):
    """树木养护措施：复壮、支撑、防腐等逐次登记。"""

    model = TreeMaintenance
    label = "树木养护措施"
    code_field = None

    @classmethod
    def prepare_instance(cls, instance, payload):
        tree_id = payload.get("tree_id", instance.tree_id)
        tree = db.session.get(TreeProfile, tree_id) if tree_id else None
        if tree is None:
            raise ValidationError("登记失败", details={"tree_id": "所属树木档案不存在"})

    @classmethod
    def list_for_tree(cls, tree_id):
        return (
            db.session.query(TreeMaintenance)
            .filter(TreeMaintenance.tree_id == tree_id)
            .order_by(TreeMaintenance.care_date.desc(), TreeMaintenance.id.desc())
            .all()
        )
