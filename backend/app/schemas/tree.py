"""树木档案与养护措施校验规则。"""

from ..constants import TREE_CARE_TYPE, TREE_PROTECTION_LEVEL, TREE_VIGOR
from .common import PHONE_PATTERN, PayloadValidator


def validate_tree(payload):
    return (
        PayloadValidator(payload)
        .string("tree_no", "树木编号", max_length=32)
        .integer("green_space_id", "所属绿地", required=True, min_value=1)
        .string("tree_species", "树种名称", required=True, max_length=96)
        .string("scientific_name", "拉丁学名", max_length=128)
        .number("dbh_cm", "胸径", min_value=0, max_value=1000)
        .number("height_m", "树高", min_value=0, max_value=200)
        .number("crown_width_m", "冠幅", min_value=0, max_value=100)
        .integer("age_years", "树龄", min_value=0, max_value=5000)
        .enum("protection_level", "保护级别", group=TREE_PROTECTION_LEVEL, default="none")
        .enum("vigor", "生长势", group=TREE_VIGOR, default="vigorous")
        .string("responsible_unit", "责任单位", required=True, max_length=128)
        .string("responsible_person", "责任人", max_length=64)
        .string("contact_phone", "联系电话", max_length=32, pattern=PHONE_PATTERN,
                pattern_message="联系电话格式不正确")
        .string("location_desc", "具体点位", max_length=255)
        .number("longitude", "经度", min_value=-180, max_value=180, digits=8)
        .number("latitude", "纬度", min_value=-90, max_value=90, digits=8)
        .date("planted_date", "栽植日期")
        .date("register_date", "建档日期", required=True)
        .text("remark", "备注", max_length=2000)
        .done()
    )


def validate_tree_maintenance(payload):
    return (
        PayloadValidator(payload)
        .enum("care_type", "养护措施类型", group=TREE_CARE_TYPE, required=True)
        .date("care_date", "实施日期", required=True)
        .text("content", "措施内容", required=True, max_length=2000)
        .string("operator", "实施人员", max_length=64)
        .string("result", "实施效果", max_length=255)
        .number("cost", "费用", min_value=0, max_value=99999999)
        .text("remark", "备注", max_length=2000)
        .done()
    )
