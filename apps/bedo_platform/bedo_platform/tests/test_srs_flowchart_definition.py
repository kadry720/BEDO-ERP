from bedo_platform.constants import (
    SRS_NODE_ACTION_PATHS,
    SRS_NODE_BMDP,
    SRS_NODE_CASE_1,
    SRS_NODE_CASE_2,
    SRS_NODE_CASE_3,
    SRS_NODE_CASE_4,
    SRS_NODE_CASES_1_2,
    SRS_NODE_CASES_3_4,
    SRS_NODE_COORDINATION,
    SRS_NODE_DEADLINE_LOCKED,
    SRS_NODE_DELIVERABLES,
    SRS_NODE_GATEWAY,
    SRS_NODE_GM_APPROVAL,
    SRS_NODE_MANAGER_APPROVAL,
    SRS_NODE_PRODUCT_DIGITAL_RELEASE,
)
from bedo_platform.services.project_service import get_srs_flowchart_definition


def test_srs_flowchart_stops_at_bmdp_and_has_no_post_bmdp_nodes():
    definition = get_srs_flowchart_definition()
    node_ids = {node["id"] for node in definition["nodes"]}
    rendered_text = str(definition)

    assert SRS_NODE_BMDP in node_ids
    assert next(node for node in definition["nodes"] if node["id"] == SRS_NODE_BMDP)["isTerminal"] is True
    assert "PBMDP" not in node_ids
    assert "PMDP" not in node_ids
    assert "GATE_2" not in node_ids
    assert "PHYSICAL_BUILD_TEST" not in node_ids
    assert not any(node_id.endswith("_HANDOVER") for node_id in node_ids)
    assert "handover" not in rendered_text.lower()


def test_display_only_srs_nodes_are_not_clickable():
    definition = get_srs_flowchart_definition()
    nodes = {node["id"]: node for node in definition["nodes"]}

    for node_id in [
        SRS_NODE_PRODUCT_DIGITAL_RELEASE,
        SRS_NODE_DELIVERABLES,
        SRS_NODE_CASES_1_2,
        SRS_NODE_CASES_3_4,
        SRS_NODE_GM_APPROVAL,
        SRS_NODE_MANAGER_APPROVAL,
        SRS_NODE_DEADLINE_LOCKED,
        SRS_NODE_ACTION_PATHS,
        SRS_NODE_CASE_1,
        SRS_NODE_CASE_2,
        SRS_NODE_CASE_3,
        SRS_NODE_CASE_4,
    ]:
        assert nodes[node_id]["kind"] in {"display", "approval"}
        assert nodes[node_id]["clickable"] is False


def test_srs_flowchart_clickable_nodes_match_permission_matrix():
    definition = get_srs_flowchart_definition()
    nodes = {node["id"]: node for node in definition["nodes"]}

    assert nodes[SRS_NODE_GATEWAY]["clickable"] is True
    assert nodes[SRS_NODE_GATEWAY]["requiredRoles"] == ["SRS Manager"]
    assert nodes[SRS_NODE_COORDINATION]["clickable"] is True
    assert nodes[SRS_NODE_BMDP]["clickable"] is True


def test_srs_flowchart_has_lanes_deadline_columns_and_edges():
    definition = get_srs_flowchart_definition()
    edges = definition["edges"]

    assert [lane["id"] for lane in definition["lanes"]] == ["operations", "srs_entry", "study_phase"]
    assert [column["id"] for column in definition["deadline_columns"]] == ["deadline_1", "deadline_2", "deadline_3"]
    assert {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_BMDP} not in edges
    assert not any(edge["from"] == SRS_NODE_BMDP for edge in edges)

    expected_edges = [
        {"from": SRS_NODE_PRODUCT_DIGITAL_RELEASE, "to": SRS_NODE_GATEWAY},
        {"from": SRS_NODE_GATEWAY, "to": SRS_NODE_COORDINATION},
        {"from": SRS_NODE_COORDINATION, "to": SRS_NODE_DELIVERABLES},
        {"from": SRS_NODE_DELIVERABLES, "to": SRS_NODE_CASES_1_2},
        {"from": SRS_NODE_DELIVERABLES, "to": SRS_NODE_CASES_3_4},
        {"from": SRS_NODE_CASES_1_2, "to": SRS_NODE_MANAGER_APPROVAL},
        {"from": SRS_NODE_CASES_3_4, "to": SRS_NODE_GM_APPROVAL},
        {"from": SRS_NODE_GM_APPROVAL, "to": SRS_NODE_MANAGER_APPROVAL},
        {"from": SRS_NODE_MANAGER_APPROVAL, "to": SRS_NODE_DEADLINE_LOCKED},
        {"from": SRS_NODE_DEADLINE_LOCKED, "to": SRS_NODE_ACTION_PATHS},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_1},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_2},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_3},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_4},
        {"from": SRS_NODE_CASE_1, "to": SRS_NODE_BMDP},
        {"from": SRS_NODE_CASE_2, "to": SRS_NODE_BMDP},
        {"from": SRS_NODE_CASE_3, "to": SRS_NODE_BMDP},
        {"from": SRS_NODE_CASE_4, "to": SRS_NODE_BMDP},
    ]
    assert edges == expected_edges
    assert {"from": SRS_NODE_CASES_1_2, "to": SRS_NODE_GM_APPROVAL} not in edges
    assert {"from": SRS_NODE_CASE_1, "to": SRS_NODE_GM_APPROVAL} not in edges
    assert {"from": SRS_NODE_CASE_2, "to": SRS_NODE_GM_APPROVAL} not in edges
