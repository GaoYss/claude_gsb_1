"""树木档案接口。"""

from flask import Blueprint, request
from sqlalchemy import func

from ..errors import NotFoundError
from ..extensions import db
from ..models import GreenSpace, TreeProfile
from ..schemas import tree_filters, validate_tree, validate_tree_maintenance
from ..services import TreeMaintenanceService, TreeService
from ..utils.pagination import paginate, parse_page_args
from ..utils.requests import json_body
from ..utils.responses import created, ok

bp = Blueprint("trees", __name__)


@bp.get("/trees")
def list_trees():
    """树木档案列表：支持保护级别、行政区、绿地、生长势与关键字检索。"""

    filters = tree_filters(request.args)
    page, page_size = parse_page_args()
    query = TreeService.list_trees(filters, request.args)
    data = paginate(query, page, page_size, serializer=TreeService.serialize_row)
    data["summary"] = TreeService.filtered_summary(filters)
    return ok(data)


@bp.get("/trees/districts")
def tree_districts():
    """有树木建档的行政区及株数，供列表按行政区筛选。"""

    rows = (
        db.session.query(GreenSpace.district, func.count(TreeProfile.id))
        .join(TreeProfile, TreeProfile.green_space_id == GreenSpace.id)
        .group_by(GreenSpace.district)
        .order_by(GreenSpace.district.asc())
        .all()
    )
    return ok({"items": [{"district": district, "count": count} for district, count in rows]})


@bp.post("/trees")
def create_tree():
    payload = validate_tree(json_body())
    tree = TreeService.create(payload)
    return created(tree.to_dict(detail=True), message="树木档案建档成功")


@bp.get("/trees/<int:tree_id>")
def get_tree(tree_id):
    return ok(TreeService.get(tree_id).to_dict(detail=True))


@bp.get("/trees/<int:tree_id>/profile")
def tree_profile(tree_id):
    """树木档案：基础信息 + 养护统计 + 全部养护措施记录。"""

    return ok(TreeService.detail(tree_id))


@bp.put("/trees/<int:tree_id>")
def update_tree(tree_id):
    payload = validate_tree(json_body())
    tree = TreeService.update(tree_id, payload)
    return ok(tree.to_dict(detail=True), message="树木档案已更新")


@bp.delete("/trees/<int:tree_id>")
def delete_tree(tree_id):
    TreeService.delete(tree_id)
    return ok(None, message="树木档案已删除")


# --------------------------------------------------------- 养护措施
@bp.get("/trees/<int:tree_id>/maintenances")
def list_tree_maintenances(tree_id):
    tree = TreeService.get(tree_id)
    items = TreeMaintenanceService.list_for_tree(tree.id)
    return ok({"items": [item.to_dict(detail=True) for item in items]})


@bp.post("/trees/<int:tree_id>/maintenances")
def create_tree_maintenance(tree_id):
    tree = TreeService.get(tree_id)
    payload = validate_tree_maintenance(json_body())
    payload["tree_id"] = tree.id
    maintenance = TreeMaintenanceService.create(payload)
    return created(maintenance.to_dict(detail=True), message="养护措施已登记")


@bp.put("/trees/<int:tree_id>/maintenances/<int:maintenance_id>")
def update_tree_maintenance(tree_id, maintenance_id):
    tree = TreeService.get(tree_id)
    maintenance = TreeMaintenanceService.get(maintenance_id)
    if maintenance.tree_id != tree.id:
        raise NotFoundError("该养护措施不属于此树木档案")
    payload = validate_tree_maintenance(json_body())
    maintenance = TreeMaintenanceService.update(maintenance_id, payload)
    return ok(maintenance.to_dict(detail=True), message="养护措施已更新")


@bp.delete("/trees/<int:tree_id>/maintenances/<int:maintenance_id>")
def delete_tree_maintenance(tree_id, maintenance_id):
    tree = TreeService.get(tree_id)
    maintenance = TreeMaintenanceService.get(maintenance_id)
    if maintenance.tree_id != tree.id:
        raise NotFoundError("该养护措施不属于此树木档案")
    TreeMaintenanceService.delete(maintenance_id)
    return ok(None, message="养护措施已删除")
