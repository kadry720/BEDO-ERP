from bedo_platform.constants import (
    SRS_NODE_ACTION_PATHS,
    SRS_NODE_BMDP,
    SRS_NODE_CASES_1_2,
    SRS_NODE_CASES_3_4,
    SRS_NODE_DEADLINE_LOCKED,
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
        SRS_NODE_CASES_1_2,
        SRS_NODE_CASES_3_4,
        SRS_NODE_DEADLINE_LOCKED,
        SRS_NODE_ACTION_PATHS,
    ]:
        assert nodes[node_id]["kind"] == "display"
        assert nodes[node_id]["clickable"] is False


def test_srs_flowchart_has_lanes_deadline_columns_and_edges():
    definition = get_srs_flowchart_definition()

    assert [lane["id"] for lane in definition["lanes"]] == ["operations", "srs_entry", "study_phase"]
    assert [column["id"] for column in definition["deadline_columns"]] == ["deadline_1", "deadline_2", "deadline_3"]
    assert {"from": SRS_NODE_ACTION_PATHS, "to": SRS_NODE_BMDP} not in definition["edges"]
    assert any(edge["to"] == SRS_NODE_BMDP for edge in definition["edges"])
