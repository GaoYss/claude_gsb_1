"""树木档案校验规则。"""

from ..constants import TREE_GROWTH_VIGOR, TREE_PROTECTION_LEVEL
from .common import PayloadValidator


def validate_tree(payload):
    return (
        PayloadValidator(payload)
        .string("code", "档案编号", max_length=32)
        .integer("green_space_id", "所在绿地", required=True, min_value=1)
        .string("species", "树种", required=True, max_length=96)
        .string("latin_name", "拉丁学名", max_length=128)
        .number("dbh_cm", "胸径", min_value=0, max_value=9999)
        .number("height_m", "树高", min_value=0, max_value=200)
        .integer("age_years", "树龄", min_value=0, max_value=9999)
        .enum("protection_level", "保护级别", group=TREE_PROTECTION_LEVEL, required=True)
        .enum("growth_vigor", "生长势", group=TREE_GROWTH_VIGOR)
        .string("responsible_unit", "责任单位", max_length=128)
        .number("longitude", "经度", min_value=-180, max_value=180, digits=6)
        .number("latitude", "纬度", min_value=-90, max_value=90, digits=6)
        .string("location_desc", "位置说明", max_length=255)
        .text("remark", "备注", max_length=2000)
        .done()
    )
