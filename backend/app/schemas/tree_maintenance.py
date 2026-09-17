"""树木养护措施校验规则。"""

from ..constants import TREE_MEASURE_TYPE
from .common import PayloadValidator


def validate_tree_maintenance(payload):
    return (
        PayloadValidator(payload)
        .integer("tree_id", "所属树木", required=True, min_value=1)
        .enum("measure_type", "措施类型", group=TREE_MEASURE_TYPE, required=True)
        .date("measure_date", "实施日期", required=True)
        .text("content", "措施内容", required=True, max_length=2000)
        .string("operator", "实施人", max_length=64)
        .text("remark", "备注", max_length=2000)
        .done()
    )
