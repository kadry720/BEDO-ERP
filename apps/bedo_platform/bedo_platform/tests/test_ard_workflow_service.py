from pathlib import Path

from bedo_platform.services import ard_workflow_service


def test_ard_workflow_doctypes_exist():
    assert Path("apps/bedo_platform/bedo_platform/ard/doctype/ard_workflow_instance/ard_workflow_instance.json").exists()
    assert Path("apps/bedo_platform/bedo_platform/ard/doctype/ard_workflow_node_state/ard_workflow_node_state.json").exists()


def test_ard_flowchart_definition_contains_required_nodes_and_edges():
    definition = ard_workflow_service.get_ard_flowchart_definition()
    node_ids = {node["id"] for node in definition["nodes"]}
    edges = {(edge["from"], edge["to"]) for edge in definition["edges"]}

    assert ard_workflow_service.ARD_NODE_HANDOVER_COMPLETE in node_ids
    assert ard_workflow_service.ARD_NODE_INTERNAL_SYNC in node_ids
    assert ard_workflow_service.ARD_NODE_OWNER_ASSIGNMENT in node_ids
    assert ard_workflow_service.ARD_NODE_TEAM_SELECTION in node_ids
    assert ard_workflow_service.ARD_NODE_PROGRESS_REVIEW in node_ids
    assert ard_workflow_service.ARD_NODE_SCMDP_SUBMISSION in node_ids
    assert (ard_workflow_service.ARD_NODE_HANDOVER_COMPLETE, ard_workflow_service.ARD_NODE_INTERNAL_SYNC) in edges


def test_handoff_completion_paths_start_ard_workflow():
    source = Path("apps/bedo_platform/bedo_platform/services/project_service.py").read_text(encoding="utf-8")

    assert "start_ard_workflow_from_handoff" in source
