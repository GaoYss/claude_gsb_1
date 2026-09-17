"""树木养护措施业务逻辑。"""

from sqlalchemy import func, or_

from ..errors import ValidationError
from ..extensions import db
from ..models import Tree, TreeMaintenance
from ..utils.sorting import parse_sort
from .base_service import BaseService
from .code_generator import daily_prefix


class TreeMaintenanceService(BaseService):
    """树木养护措施：复壮、支撑、防腐等措施逐次登记。"""

    model = TreeMaintenance
    label = "树木养护措施"
    code_field = "record_no"
    code_width = 3

    SORTABLE = {
        "measure_date": TreeMaintenance.measure_date,
        "created_at": TreeMaintenance.created_at,
    }

    @classmethod
    def code_prefix(cls):
        return daily_prefix("TM")

    # ------------------------------------------------------------ 校验
    @classmethod
    def prepare_instance(cls, instance, payload):
        tree_id = payload.get("tree_id", instance.tree_id)
        tree = db.session.get(Tree, tree_id) if tree_id else None
        if tree is None:
            raise ValidationError("登记失败", details={"tree_id": "所选树木不存在"})

        measure_date = payload.get("measure_date", instance.measure_date)
        established = tree.green_space.established_date if tree.green_space else None
        if measure_date and established and measure_date < established:
            raise ValidationError(
                "登记失败",
                details={"measure_date": f"实施日期不能早于绿地建成日期 {established}"},
            )

    # ------------------------------------------------------------ 查询
    @staticmethod
    def _apply_filters(query, filters):
        if filters.get("tree_id"):
            query = query.filter(TreeMaintenance.tree_id == filters["tree_id"])
        if filters.get("measure_type"):
            query = query.filter(TreeMaintenance.measure_type == filters["measure_type"])
        if filters.get("date_from"):
            query = query.filter(TreeMaintenance.measure_date >= filters["date_from"])
        if filters.get("date_to"):
            query = query.filter(TreeMaintenance.measure_date <= filters["date_to"])
        keyword = filters.get("keyword")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    TreeMaintenance.record_no.like(like),
                    TreeMaintenance.content.like(like),
                    TreeMaintenance.operator.like(like),
                )
            )
        return query

    @classmethod
    def list_maintenances(cls, filters, args):
        query = cls._apply_filters(db.session.query(TreeMaintenance), filters)
        return query.order_by(
            parse_sort(args, cls.SORTABLE, TreeMaintenance.measure_date.desc())
        )

    @classmethod
    def detail(cls, obj_id):
        return cls.get(obj_id).to_dict(detail=True)
