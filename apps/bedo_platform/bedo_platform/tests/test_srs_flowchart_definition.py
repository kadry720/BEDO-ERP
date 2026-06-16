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
    SRS_NODE_DUAL_GATE_APPROVAL,
    SRS_NODE_EXTENSION_DEADLINE,
    SRS_NODE_GATEWAY,
    SRS_NODE_GATE_2_PMDP,
    SRS_NODE_GM_APPROVAL,
    SRS_NODE_MANAGER_APPROVAL,
    SRS_NODE_PHYSICAL_BUILD_TEST,
    SRS_NODE_PMDP,
    SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
    SRS_NODE_PRODUCT_DIGITAL_RELEASE,
    SRS_NODE_SRS_DIRECTOR_APPROVAL,
)
from bedo_platform.services.project_service import get_srs_flowchart_definition


def test_srs_flowchart_uses_dual_gate_and_case_3_branch():
    definition = get_srs_flowchart_definition()
    node_ids = {node["id"] for node in definition["nodes"]}

    assert SRS_NODE_DUAL_GATE_APPROVAL in node_ids
    assert SRS_NODE_GATE_2_PMDP in node_ids
    assert SRS_NODE_PMDP_DUAL_GATE_APPROVAL in node_ids
    assert SRS_NODE_PHYSICAL_BUILD_TEST in node_ids
    assert SRS_NODE_EXTENSION_DEADLINE in node_ids
    assert SRS_NODE_SRS_DIRECTOR_APPROVAL in node_ids
    assert SRS_NODE_PMDP in node_ids
    assert SRS_NODE_CASES_1_2 not in node_ids
    assert SRS_NODE_CASES_3_4 not in node_ids
    assert SRS_NODE_GM_APPROVAL not in node_ids
    assert SRS_NODE_MANAGER_APPROVAL not in node_ids


def test_display_only_srs_nodes_are_not_clickable():
    definition = get_srs_flowchart_definition()
    nodes = {node["id"]: node for node in definition["nodes"]}

    for node_id in [
        SRS_NODE_PRODUCT_DIGITAL_RELEASE,
        SRS_NODE_DUAL_GATE_APPROVAL,
        SRS_NODE_DEADLINE_LOCKED,
        SRS_NODE_ACTION_PATHS,
        SRS_NODE_CASE_1,
        SRS_NODE_CASE_2,
        SRS_NODE_CASE_3,
        SRS_NODE_CASE_4,
        SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
        SRS_NODE_EXTENSION_DEADLINE,
        SRS_NODE_SRS_DIRECTOR_APPROVAL,
    ]:
        assert nodes[node_id]["kind"] in {"display", "approval", "action"}
        assert nodes[node_id]["clickable"] is False


def test_srs_flowchart_clickable_nodes_match_permission_matrix():
    definition = get_srs_flowchart_definition()
    nodes = {node["id"]: node for node in definition["nodes"]}

    assert nodes[SRS_NODE_GATEWAY]["clickable"] is True
    assert nodes[SRS_NODE_GATEWAY]["requiredRoles"] == ["SRS Manager"]
    assert nodes[SRS_NODE_COORDINATION]["clickable"] is True
    assert nodes[SRS_NODE_DELIVERABLES]["clickable"] is True
    assert nodes[SRS_NODE_GATE_2_PMDP]["clickable"] is True
    assert nodes[SRS_NODE_PHYSICAL_BUILD_TEST]["clickable"] is True
    assert nodes[SRS_NODE_PMDP]["clickable"] is True
    assert nodes[SRS_NODE_BMDP]["clickable"] is True


def test_srs_flowchart_has_lanes_deadline_columns_and_edges():
    definition = get_srs_flowchart_definition()
    edges = definition["edges"]

    assert [lane["id"] for lane in definition["lanes"]] == ["operations", "srs_entry", "study_phase"]
    assert [column["id"] for column in definition["deadline_columns"]] == ["deadline_1", "deadline_2", "deadline_3", "deadline_4"]
    assert not any(edge["from"] == SRS_NODE_BMDP for edge in edges)

    assert edges == [
        {"from": SRS_NODE_PRODUCT_DIGITAL_RELEASE, "to": SRS_NODE_GATEWAY},
        {"from": SRS_NODE_GATEWAY, "to": SRS_NODE_COORDINATION},
        {"from": SRS_NODE_COORDINATION, "to": SRS_NODE_DELIVERABLES},
        {"from": SRS_NODE_DELIVERABLES, "to": SRS_NODE_DUAL_GATE_APPROVAL},
        {"from": SRS_NODE_DUAL_GATE_APPROVAL, "to": SRS_NODE_DEADLINE_LOCKED},
        {"from": SRS_NODE_DEADLINE_LOCKED, "to": SRS_NODE_ACTION_PATHS},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_1},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_2},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_3},
        {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_CASE_4},
        {"from": SRS_NODE_CASE_1, "to": SRS_NODE_BMDP},
        {"from": SRS_NODE_CASE_2, "to": SRS_NODE_BMDP},
        {"from": SRS_NODE_CASE_4, "to": SRS_NODE_BMDP},
        {"from": SRS_NODE_CASE_3, "to": SRS_NODE_GATE_2_PMDP},
        {"from": SRS_NODE_GATE_2_PMDP, "to": SRS_NODE_PMDP_DUAL_GATE_APPROVAL},
        {"from": SRS_NODE_PMDP_DUAL_GATE_APPROVAL, "to": SRS_NODE_PHYSICAL_BUILD_TEST},
        {"from": SRS_NODE_PHYSICAL_BUILD_TEST, "to": SRS_NODE_EXTENSION_DEADLINE},
        {"from": SRS_NODE_EXTENSION_DEADLINE, "to": SRS_NODE_SRS_DIRECTOR_APPROVAL},
        {"from": SRS_NODE_SRS_DIRECTOR_APPROVAL, "to": SRS_NODE_PHYSICAL_BUILD_TEST},
        {"from": SRS_NODE_PHYSICAL_BUILD_TEST, "to": SRS_NODE_PMDP},
        {"from": SRS_NODE_PMDP, "to": SRS_NODE_BMDP},
    ]


def test_srs_flowchart_ends_at_bmdp():
    definition = get_srs_flowchart_definition()
    node_ids = {node["id"] for node in definition["nodes"]}

    assert SRS_NODE_BMDP in node_ids
    assert "COMMAND_CENTER_APPROVAL" not in node_ids
    assert "FINAL_GM_APPROVAL" not in node_ids
