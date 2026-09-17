"""树木档案与树木养护措施接口。"""

from flask import Blueprint, request

from ..schemas import (
    tree_filters,
    tree_maintenance_filters,
    validate_tree,
    validate_tree_maintenance,
)
from ..services import TreeMaintenanceService, TreeService
from ..utils.pagination import paginate, parse_page_args
from ..utils.requests import json_body, query_flag
from ..utils.responses import created, ok

bp = Blueprint("trees", __name__)


# ---------------------------------------------------------------- 树木档案
@bp.get("/trees")
def list_trees():
    """档案列表：支持关键字、保护级别、生长势、行政区、所在绿地过滤。"""

    filters = tree_filters(request.args)
    page, page_size = parse_page_args()
    query = TreeService.list_trees(filters, request.args)
    data = paginate(query, page, page_size, serializer=TreeService.serialize_row)
    data["summary"] = TreeService.summary(filters)
    return ok(data)


@bp.get("/trees/summary")
def tree_summary():
    return ok(TreeService.summary(tree_filters(request.args)))


@bp.post("/trees")
def create_tree():
    payload = validate_tree(json_body())
    tree = TreeService.create(payload)
    return created(tree.to_dict(detail=True), message="树木档案创建成功")


@bp.get("/trees/<int:tree_id>")
def get_tree(tree_id):
    """档案详情：台账字段 + 措施统计 + 逐次措施记录。"""

    return ok(TreeService.detail(tree_id))


@bp.put("/trees/<int:tree_id>")
def update_tree(tree_id):
    payload = validate_tree(json_body())
    tree = TreeService.update(tree_id, payload)
    return ok(tree.to_dict(detail=True), message="树木档案已更新")


@bp.delete("/trees/<int:tree_id>")
def delete_tree(tree_id):
    """删除档案。已登记养护措施时需显式 force=true 才会级联清理。"""

    force = query_flag("force")
    TreeService.delete(tree_id, force=force)
    return ok(None, message="树木档案及其养护措施已删除" if force else "树木档案已删除")


# ---------------------------------------------------------------- 养护措施
@bp.get("/tree-maintenances")
def list_tree_maintenances():
    filters = tree_maintenance_filters(request.args)
    page, page_size = parse_page_args()
    query = TreeMaintenanceService.list_maintenances(filters, request.args)
    return ok(paginate(query, page, page_size))


@bp.post("/tree-maintenances")
def create_tree_maintenance():
    payload = validate_tree_maintenance(json_body())
    maintenance = TreeMaintenanceService.create(payload)
    return created(maintenance.to_dict(detail=True), message="树木养护措施登记成功")


@bp.get("/tree-maintenances/<int:maintenance_id>")
def get_tree_maintenance(maintenance_id):
    return ok(TreeMaintenanceService.detail(maintenance_id))


@bp.put("/tree-maintenances/<int:maintenance_id>")
def update_tree_maintenance(maintenance_id):
    payload = validate_tree_maintenance(json_body())
    maintenance = TreeMaintenanceService.update(maintenance_id, payload)
    return ok(maintenance.to_dict(detail=True), message="树木养护措施已更新")


@bp.delete("/tree-maintenances/<int:maintenance_id>")
def delete_tree_maintenance(maintenance_id):
    TreeMaintenanceService.delete(maintenance_id)
    return ok(None, message="树木养护措施已删除")
