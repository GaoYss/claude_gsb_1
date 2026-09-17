"""树木档案与树木养护措施接口测试。"""

from datetime import date


def tree_payload(space_id, **overrides):
    payload = {
        "green_space_id": space_id,
        "species": "香樟",
        "latin_name": "Cinnamomum camphora",
        "dbh_cm": 86.5,
        "height_m": 16.0,
        "age_years": 210,
        "protection_level": "level2",
        "growth_vigor": "normal",
        "responsible_unit": "杭州市绿化管理站",
        "longitude": 120.1551,
        "latitude": 30.2742,
        "location_desc": "主入口东侧约 30 米",
    }
    payload.update(overrides)
    return payload


def measure_payload(tree_id, **overrides):
    payload = {
        "tree_id": tree_id,
        "measure_type": "rejuvenation",
        "measure_date": "2026-04-10",
        "content": "开挖放射状复壮沟 4 条，回填腐殖土",
        "operator": "王海涛",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------- 树木档案
def test_create_tree_generates_code_with_year_prefix(api, make_space):
    space = make_space()
    data = api.data(api.post("/api/v1/trees", tree_payload(space.id)), 201)
    assert data["code"] == f"TR-{date.today():%Y}-0001"
    assert data["species"] == "香樟"
    assert data["protection_level_label"] == "二级古树"
    assert data["growth_vigor_label"] == "正常"
    assert data["dbh_cm"] == 86.5
    assert data["longitude"] == 120.1551
    assert data["green_space"]["id"] == space.id


def test_create_tree_reports_field_errors_together(api, make_space):
    space = make_space()
    response = api.post("/api/v1/trees", {
        "green_space_id": space.id,
        "species": "",
        "protection_level": "level9",
        "growth_vigor": "unknown",
        "age_years": -3,
        "longitude": 200,
        "latitude": -100,
    })
    assert response.status_code == 422
    details = response.get_json()["data"]
    assert set(details) == {
        "species", "protection_level", "growth_vigor", "age_years", "longitude", "latitude"
    }
    assert "取值不合法" in details["protection_level"]


def test_create_tree_requires_existing_green_space(api):
    response = api.post("/api/v1/trees", tree_payload(9999))
    assert response.status_code == 422
    assert "绿地" in response.get_json()["data"]["green_space_id"]


def test_list_trees_filters_by_protection_level_and_district(api, make_space, make_tree):
    space_west = make_space(name="西湖绿地", district="西湖区")
    space_north = make_space(name="拱墅绿地", district="拱墅区")
    make_tree(space_west, protection_level="level1")
    make_tree(space_west, protection_level="famous")
    make_tree(space_north, protection_level="level1")

    data = api.data(api.get("/api/v1/trees", protection_level="level1"))
    assert data["meta"]["total"] == 2
    assert {item["protection_level"] for item in data["items"]} == {"level1"}

    data = api.data(api.get("/api/v1/trees", district="西湖区"))
    assert data["meta"]["total"] == 2
    assert {item["green_space"]["district"] for item in data["items"]} == {"西湖区"}

    data = api.data(api.get("/api/v1/trees", protection_level="level1", district="拱墅区"))
    assert data["meta"]["total"] == 1
    assert data["items"][0]["green_space"]["district"] == "拱墅区"


def test_list_trees_supports_keyword_and_summary(api, make_space, make_tree, make_tree_maintenance):
    space = make_space(district="西湖区")
    tree = make_tree(space, species="银杏", responsible_unit="区园林绿化发展中心")
    make_tree(space, protection_level="ordinary", growth_vigor="vigorous")
    make_tree_maintenance(tree)

    data = api.data(api.get("/api/v1/trees", keyword="银杏"))
    assert data["meta"]["total"] == 1
    assert data["items"][0]["species"] == "银杏"
    assert data["items"][0]["statistics"]["maintenance_count"] == 1

    summary = data["summary"]
    assert summary["total_count"] == 1
    assert summary["district_count"] == 1
    assert summary["maintenance_count"] == 1
    assert summary["by_level"][0]["label"] == "二级古树"


def test_tree_detail_aggregates_maintenances(api, make_tree, make_tree_maintenance):
    tree = make_tree()
    make_tree_maintenance(tree, measure_type="support", measure_date=date(2026, 5, 1),
                          content="加装钢管支撑 2 处")
    make_tree_maintenance(tree, measure_date=date(2026, 4, 10))

    data = api.data(api.get(f"/api/v1/trees/{tree.id}"))
    assert data["tree"]["code"] == tree.code
    assert data["statistics"]["maintenance_count"] == 2
    assert data["statistics"]["last_measure_date"] == "2026-05-01"
    type_map = {item["value"]: item["count"] for item in data["statistics"]["by_measure_type"]}
    assert type_map == {"rejuvenation": 1, "support": 1}
    # 措施按实施日期倒序逐次排列
    assert [item["measure_type"] for item in data["maintenances"]] == ["support", "rejuvenation"]
    assert data["maintenances"][0]["measure_type_label"] == "支撑加固"


def test_update_tree_keeps_code_immutable(api, make_tree):
    tree = make_tree()
    data = api.data(api.put(f"/api/v1/trees/{tree.id}", {
        "green_space_id": tree.green_space_id,
        "species": "银杏",
        "protection_level": "level1",
        "code": "TR-2099-9999",
    }))
    assert data["code"] == tree.code
    assert data["species"] == "银杏"
    assert data["protection_level"] == "level1"


def test_delete_tree_is_blocked_until_force(api, make_tree, make_tree_maintenance):
    tree = make_tree()
    make_tree_maintenance(tree)

    response = api.delete(f"/api/v1/trees/{tree.id}")
    assert response.status_code == 409
    assert response.get_json()["data"]["tree_maintenance"] == 1

    api.data(api.delete(f"/api/v1/trees/{tree.id}", force="true"))
    assert api.get(f"/api/v1/trees/{tree.id}").status_code == 404
    assert api.get(f"/api/v1/tree-maintenances", tree_id=tree.id) .get_json()["data"]["meta"]["total"] == 0


def test_green_space_delete_counts_trees(api, make_tree):
    tree = make_tree()
    space_id = tree.green_space_id

    response = api.delete(f"/api/v1/green-spaces/{space_id}")
    assert response.status_code == 409
    assert response.get_json()["data"]["tree"] == 1

    api.data(api.delete(f"/api/v1/green-spaces/{space_id}", force="true"))
    assert api.get(f"/api/v1/trees/{tree.id}").status_code == 404


# ---------------------------------------------------------------- 树木养护措施
def test_create_measure_generates_daily_code(api, make_tree):
    tree = make_tree()
    data = api.data(api.post("/api/v1/tree-maintenances", measure_payload(tree.id)), 201)
    assert data["record_no"] == f"TM-{date.today():%Y%m%d}-001"
    assert data["measure_type_label"] == "复壮"
    assert data["tree"]["id"] == tree.id


def test_measure_requires_existing_tree_and_valid_fields(api, make_tree):
    response = api.post("/api/v1/tree-maintenances", measure_payload(9999))
    assert response.status_code == 422
    assert "树木" in response.get_json()["data"]["tree_id"]

    tree = make_tree()
    response = api.post("/api/v1/tree-maintenances",
                        measure_payload(tree.id, measure_type="magic", content=""))
    assert response.status_code == 422
    details = response.get_json()["data"]
    assert set(details) == {"measure_type", "content"}


def test_measure_date_not_before_green_space_established(api, make_space, make_tree):
    space = make_space(established_date=date(2020, 1, 1))
    tree = make_tree(space)
    response = api.post("/api/v1/tree-maintenances",
                        measure_payload(tree.id, measure_date="2019-12-31"))
    assert response.status_code == 422
    assert "不能早于绿地建成日期" in response.get_json()["data"]["measure_date"]


def test_measure_list_filters_by_tree_and_type(api, make_tree, make_tree_maintenance):
    tree = make_tree()
    other = make_tree(species="银杏")
    make_tree_maintenance(tree, measure_type="support")
    make_tree_maintenance(tree, measure_type="anticorrosion")
    make_tree_maintenance(other, measure_type="support")

    data = api.data(api.get("/api/v1/tree-maintenances", tree_id=tree.id))
    assert data["meta"]["total"] == 2

    data = api.data(api.get("/api/v1/tree-maintenances",
                            tree_id=tree.id, measure_type="support"))
    assert data["meta"]["total"] == 1
    assert data["items"][0]["measure_type"] == "support"


def test_update_and_delete_measure(api, make_tree_maintenance):
    maintenance = make_tree_maintenance()
    data = api.data(api.put(f"/api/v1/tree-maintenances/{maintenance.id}", {
        "tree_id": maintenance.tree_id,
        "measure_type": "anticorrosion",
        "measure_date": "2026-05-20",
        "content": "清理腐朽树洞，涂刷防腐剂",
    }))
    assert data["measure_type"] == "anticorrosion"
    assert data["record_no"] == maintenance.record_no

    api.data(api.delete(f"/api/v1/tree-maintenances/{maintenance.id}"))
    assert api.get(f"/api/v1/tree-maintenances/{maintenance.id}").status_code == 404
