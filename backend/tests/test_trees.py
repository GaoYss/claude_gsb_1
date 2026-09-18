"""树木档案与养护措施接口测试。"""

from datetime import date


def tree_payload(space_id, **overrides):
    payload = {
        "green_space_id": space_id,
        "tree_species": "香樟",
        "scientific_name": "Cinnamomum camphora",
        "dbh_cm": 62,
        "height_m": 15,
        "crown_width_m": 9,
        "age_years": 260,
        "protection_level": "level1",
        "vigor": "vigorous",
        "responsible_unit": "杭州市园林文物局",
        "responsible_person": "沈建国",
        "contact_phone": "0571-85112233",
        "location_desc": "广场中轴北端喷泉西侧",
        "longitude": 120.16921,
        "latitude": 30.27405,
        "planted_date": "1766-01-01",
        "register_date": "2024-05-18",
    }
    payload.update(overrides)
    return payload


def care_payload(**overrides):
    payload = {
        "care_type": "rejuvenate",
        "care_date": "2026-03-21",
        "content": "树冠打孔注灌复壮基质，疏松根际土壤",
        "operator": "李建民",
        "result": "萌出新梢，树势有所恢复",
        "cost": 3600,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------- 建档
def test_create_tree_generates_code_and_labels(api, make_space):
    space = make_space()
    data = api.data(api.post("/api/v1/trees", tree_payload(space.id)), 201)
    assert data["tree_no"].startswith("TR-")
    assert data["tree_species"] == "香樟"
    assert data["dbh_cm"] == 62.0
    assert data["age_years"] == 260
    assert data["protection_level"] == "level1"
    assert data["protection_level_label"] == "一级保护"
    assert data["vigor_label"] == "长势正常"
    assert data["green_space"]["id"] == space.id
    assert data["longitude"] == 120.16921
    assert data["latitude"] == 30.27405
    assert data["maintenances"] == []


def test_tree_required_fields_and_enum_validated(api, make_space):
    space = make_space()
    response = api.post("/api/v1/trees", {
        "green_space_id": space.id,
        "protection_level": "national",
        "dbh_cm": -5,
        "register_date": "2024-05-18",
    })
    assert response.status_code == 422
    details = response.get_json()["data"]
    assert "tree_species" in details
    assert "responsible_unit" in details
    assert "protection_level" in details
    assert "dbh_cm" in details


def test_tree_coordinates_must_come_together(api, make_space):
    space = make_space()
    response = api.post("/api/v1/trees", tree_payload(space.id, latitude=None))
    assert response.status_code == 422
    assert "经纬度" in response.get_json()["data"]["longitude"]


def test_tree_coordinate_range_validated(api, make_space):
    space = make_space()
    response = api.post(
        "/api/v1/trees", tree_payload(space.id, longitude=200, latitude=30.27)
    )
    assert response.status_code == 422
    assert "longitude" in response.get_json()["data"]


def test_planted_date_cannot_be_after_register_date(api, make_space):
    space = make_space()
    response = api.post(
        "/api/v1/trees",
        tree_payload(space.id, planted_date="2026-01-01", register_date="2024-01-01"),
    )
    assert response.status_code == 422
    assert "planted_date" in response.get_json()["data"]


def test_tree_must_reference_existing_green_space(api, make_space):
    make_space()
    response = api.post("/api/v1/trees", tree_payload(99999))
    assert response.status_code == 422
    assert "green_space_id" in response.get_json()["data"]


def test_tree_code_is_immutable_after_creation(api, make_tree):
    tree = make_tree()
    data = api.data(api.put(f"/api/v1/trees/{tree.id}", {
        "green_space_id": tree.green_space_id,
        "tree_no": "TR-9999-9999",
        "tree_species": tree.tree_species,
        "protection_level": tree.protection_level,
        "vigor": tree.vigor,
        "responsible_unit": tree.responsible_unit,
        "register_date": "2026-01-10",
        "dbh_cm": 50,
    }))
    assert data["tree_no"] == tree.tree_no
    assert data["dbh_cm"] == 50.0


# --------------------------------------------------------------- 检索
def test_list_filters_by_protection_level_and_district(api, make_space, make_tree):
    space_a = make_space(name="拱墅绿地A", district="拱墅区")
    space_b = make_space(name="余杭绿地B", district="余杭区")
    make_tree(space=space_a, protection_level="level1")
    make_tree(space=space_a, protection_level="none")
    make_tree(space=space_b, protection_level="level1")

    data = api.data(api.get("/api/v1/trees", district="拱墅区"))
    assert data["meta"]["total"] == 2
    assert {item["green_space"]["id"] for item in data["items"]} == {space_a.id}

    data = api.data(api.get("/api/v1/trees", protection_level="level1"))
    assert data["meta"]["total"] == 2

    data = api.data(api.get(
        "/api/v1/trees", district="拱墅区", protection_level="level1"))
    assert data["meta"]["total"] == 1
    assert data["summary"]["total"] == 1
    assert data["summary"]["protection_level_summary"]["level1"] == 1
    assert data["summary"]["protection_level_summary"]["none"] == 0


def test_list_filters_by_green_space_vigor_and_keyword(api, make_space, make_tree):
    space = make_space(name="目标绿地")
    make_tree(space=space, tree_species="古银杏", vigor="weak", protection_level="famous")
    make_tree(space=space, tree_species="香樟", vigor="vigorous")

    data = api.data(api.get("/api/v1/trees", green_space_id=space.id))
    assert data["meta"]["total"] == 2

    data = api.data(api.get("/api/v1/trees", green_space_id=space.id, vigor="weak"))
    assert data["meta"]["total"] == 1
    assert data["items"][0]["tree_species"] == "古银杏"

    data = api.data(api.get("/api/v1/trees", keyword="银杏"))
    assert data["meta"]["total"] == 1


def test_tree_districts_endpoint(api, make_space, make_tree):
    space_a = make_space(name="绿地A", district="拱墅区")
    space_b = make_space(name="绿地B", district="滨江区")
    make_tree(space=space_a)
    make_tree(space=space_a)
    make_tree(space=space_b)

    data = api.data(api.get("/api/v1/trees/districts"))
    counts = {item["district"]: item["count"] for item in data["items"]}
    assert counts["拱墅区"] == 2
    assert counts["滨江区"] == 1


def test_list_rows_include_maintenance_stats(api, make_tree, make_tree_care):
    tree = make_tree()
    make_tree_care(tree=tree, care_date=date(2026, 1, 1))
    make_tree_care(tree=tree, care_date=date(2026, 5, 1))

    data = api.data(api.get("/api/v1/trees"))
    row = next(item for item in data["items"] if item["id"] == tree.id)
    assert row["maintenance_count"] == 2
    assert row["last_care_date"] == "2026-05-01"


# --------------------------------------------------------------- 养护措施
def test_profile_aggregates_maintenances(api, make_tree, make_tree_care):
    tree = make_tree()
    make_tree_care(tree=tree, care_type="rejuvenate", care_date=date(2026, 1, 10))
    make_tree_care(tree=tree, care_type="support", care_date=date(2026, 5, 6))

    data = api.data(api.get(f"/api/v1/trees/{tree.id}/profile"))
    assert data["tree"]["id"] == tree.id
    assert data["statistics"]["maintenance_count"] == 2
    assert data["statistics"]["last_care_date"] == "2026-05-06"
    types = {item["care_type"]: item["count"] for item in data["care_summary"]}
    assert types["rejuvenate"] == 1 and types["support"] == 1
    # 措施按实施日期倒序
    maintenances = data["tree"]["maintenances"]
    assert [item["care_date"] for item in maintenances] == ["2026-05-06", "2026-01-10"]
    assert maintenances[0]["care_type_label"] == "支撑加固"


def test_create_maintenance_under_tree(api, make_tree):
    tree = make_tree()
    data = api.data(
        api.post(f"/api/v1/trees/{tree.id}/maintenances", care_payload()), 201
    )
    assert data["tree_id"] == tree.id
    assert data["care_type_label"] == "复壮养护"
    assert data["cost"] == 3600.0

    listed = api.data(api.get(f"/api/v1/trees/{tree.id}/maintenances"))
    assert len(listed["items"]) == 1


def test_maintenance_requires_valid_type_and_date(api, make_tree):
    tree = make_tree()
    response = api.post(f"/api/v1/trees/{tree.id}/maintenances", {
        "content": "缺少类型与日期",
    })
    assert response.status_code == 422
    details = response.get_json()["data"]
    assert "care_type" in details and "care_date" in details


def test_create_maintenance_on_missing_tree_404(api, make_tree):
    make_tree()
    assert api.post("/api/v1/trees/99999/maintenances", care_payload()).status_code == 404


def test_update_and_delete_maintenance(api, make_tree, make_tree_care):
    tree = make_tree()
    care = make_tree_care(tree=tree)

    data = api.data(api.put(
        f"/api/v1/trees/{tree.id}/maintenances/{care.id}",
        care_payload(care_type="antisepsis", result="腐朽部位已封闭"),
    ))
    assert data["care_type"] == "antisepsis"
    assert data["result"] == "腐朽部位已封闭"

    api.delete(f"/api/v1/trees/{tree.id}/maintenances/{care.id}")
    listed = api.data(api.get(f"/api/v1/trees/{tree.id}/maintenances"))
    assert listed["items"] == []


def test_maintenance_cross_tree_access_is_404(api, make_tree, make_tree_care):
    tree_a = make_tree(tree_species="甲树")
    tree_b = make_tree(tree_species="乙树")
    care = make_tree_care(tree=tree_a)

    assert api.put(
        f"/api/v1/trees/{tree_b.id}/maintenances/{care.id}", care_payload()
    ).status_code == 404
    assert api.delete(
        f"/api/v1/trees/{tree_b.id}/maintenances/{care.id}"
    ).status_code == 404


def test_deleting_tree_cascades_maintenances(api, make_tree, make_tree_care):
    tree = make_tree()
    make_tree_care(tree=tree)
    make_tree_care(tree=tree)

    api.delete(f"/api/v1/trees/{tree.id}")
    assert api.get(f"/api/v1/trees/{tree.id}").status_code == 404
    from app.models import TreeMaintenance

    assert TreeMaintenance.query.count() == 0


# --------------------------------------------------------------- 与绿地联动
def test_green_space_delete_protected_by_trees(api, make_space, make_tree):
    space = make_space()
    make_tree(space=space)
    response = api.delete(f"/api/v1/green-spaces/{space.id}")
    assert response.status_code == 409
    assert response.get_json()["data"]["tree_profile"] == 1

    api.delete(f"/api/v1/green-spaces/{space.id}", force=True)
    assert api.get(f"/api/v1/trees").get_json()["data"]["meta"]["total"] == 0


def test_green_space_profile_contains_trees(api, make_space, make_tree):
    space = make_space()
    make_tree(space=space, protection_level="famous")
    make_tree(space=space, protection_level="none")

    data = api.data(api.get(f"/api/v1/green-spaces/{space.id}/profile"))
    assert data["statistics"]["tree_count"] == 2
    assert data["statistics"]["protected_tree_count"] == 1
    assert len(data["recent_trees"]) == 2
