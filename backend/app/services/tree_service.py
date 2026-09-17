"""树木档案业务逻辑。"""

from sqlalchemy import func, or_

from ..constants import ENUM_GROUPS
from ..errors import ConflictError, ValidationError
from ..extensions import db
from ..models import GreenSpace, Tree, TreeMaintenance
from ..utils.dates import format_date
from ..utils.sorting import parse_sort
from .base_service import BaseService
from .code_generator import year_prefix


class TreeService(BaseService):
    """树木档案：一树一档，关联所在绿地，汇总养护措施。"""

    model = Tree
    label = "树木档案"
    code_field = "code"
    code_width = 4

    SORTABLE = {
        "code": Tree.code,
        "species": Tree.species,
        "age_years": Tree.age_years,
        "dbh_cm": Tree.dbh_cm,
        "created_at": Tree.created_at,
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

    # ------------------------------------------------------------ 查询
    @staticmethod
    def _apply_filters(query, filters):
        if filters.get("green_space_id"):
            query = query.filter(Tree.green_space_id == filters["green_space_id"])
        if filters.get("protection_level"):
            query = query.filter(Tree.protection_level == filters["protection_level"])
        if filters.get("growth_vigor"):
            query = query.filter(Tree.growth_vigor == filters["growth_vigor"])
        if filters.get("district"):
            query = query.filter(Tree.green_space.has(GreenSpace.district == filters["district"]))
        keyword = filters.get("keyword")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    Tree.code.like(like),
                    Tree.species.like(like),
                    Tree.latin_name.like(like),
                    Tree.responsible_unit.like(like),
                    Tree.location_desc.like(like),
                )
            )
        return query

    @classmethod
    def list_trees(cls, filters, args):
        """列表查询：用相关子查询带出各树木的措施统计，避免 N+1。"""

        maintenance_count = (
            db.select(func.count(TreeMaintenance.id))
            .where(TreeMaintenance.tree_id == Tree.id)
            .correlate(Tree)
            .scalar_subquery()
        )
        last_measure = (
            db.select(func.max(TreeMaintenance.measure_date))
            .where(TreeMaintenance.tree_id == Tree.id)
            .correlate(Tree)
            .scalar_subquery()
        )
        query = db.session.query(
            Tree,
            maintenance_count.label("maintenance_count"),
            last_measure.label("last_measure_date"),
        )
        query = cls._apply_filters(query, filters)
        query = query.order_by(parse_sort(args, cls.SORTABLE, Tree.code.asc()))
        return query

    @classmethod
    def serialize_row(cls, row):
        tree, maintenance_count, last_measure_date = row
        data = tree.to_dict()
        data["statistics"] = {
            "maintenance_count": maintenance_count or 0,
            "last_measure_date": format_date(last_measure_date),
        }
        return data

    @classmethod
    def summary(cls, filters):
        """树木汇总：总量、保护级别分布、覆盖行政区与措施次数。"""

        total = cls._apply_filters(db.session.query(func.count(Tree.id)), filters).scalar() or 0

        level_rows = (
            cls._apply_filters(
                db.session.query(Tree.protection_level, func.count(Tree.id)), filters
            )
            .group_by(Tree.protection_level)
            .all()
        )
        by_level = [
            {
                "value": value,
                "label": ENUM_GROUPS["tree_protection_level"].label(value),
                "count": count,
            }
            for value, count in level_rows
        ]

        district_count = (
            cls._apply_filters(
                db.session.query(func.count(func.distinct(GreenSpace.district)))
                .select_from(Tree)
                .join(GreenSpace, Tree.green_space_id == GreenSpace.id),
                filters,
            ).scalar()
            or 0
        )

        maintenance_count = (
            cls._apply_filters(
                db.session.query(func.count(TreeMaintenance.id))
                .select_from(TreeMaintenance)
                .join(Tree, TreeMaintenance.tree_id == Tree.id),
                filters,
            ).scalar()
            or 0
        )

        return {
            "total_count": total,
            "district_count": district_count,
            "maintenance_count": maintenance_count,
            "by_level": by_level,
        }

    @classmethod
    def detail(cls, obj_id):
        """档案详情：台账字段 + 措施统计 + 逐次措施记录。"""

        tree = cls.get(obj_id)
        type_rows = (
            db.session.query(TreeMaintenance.measure_type, func.count(TreeMaintenance.id))
            .filter(TreeMaintenance.tree_id == tree.id)
            .group_by(TreeMaintenance.measure_type)
            .all()
        )
        # 关联关系已按实施日期倒序排列
        maintenances = list(tree.maintenances)
        return {
            "tree": tree.to_dict(detail=True),
            "statistics": {
                "maintenance_count": len(maintenances),
                "last_measure_date": format_date(
                    maintenances[0].measure_date if maintenances else None
                ),
                "by_measure_type": [
                    {
                        "value": value,
                        "label": ENUM_GROUPS["tree_measure_type"].label(value),
                        "count": count,
                    }
                    for value, count in type_rows
                ],
            },
            "maintenances": [item.to_dict(detail=True) for item in maintenances],
        }

    # ------------------------------------------------------------ 写入
    @classmethod
    def delete(cls, obj_id, force=False):
        tree = cls.get(obj_id)
        maintenance_count = (
            db.session.query(func.count(TreeMaintenance.id))
            .filter(TreeMaintenance.tree_id == tree.id)
            .scalar()
            or 0
        )
        if maintenance_count and not force:
            raise ConflictError(
                f"该树木已登记养护措施 {maintenance_count} 次，删除将一并清除，请确认后重试",
                details={"tree_maintenance": maintenance_count},
            )
        db.session.delete(tree)
        db.session.commit()
        return {"tree_maintenance": maintenance_count}
