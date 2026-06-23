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


def test_ard_workflow_doctypes_include_team_members():
    assert Path("apps/bedo_platform/bedo_platform/ard/doctype/ard_workflow_team_member/ard_workflow_team_member.json").exists()


def test_ard_workflow_service_exposes_core_transitions():
    assert callable(ard_workflow_service.get_ard_workspace)
    assert callable(ard_workflow_service.schedule_internal_sync_meeting)
    assert callable(ard_workflow_service.complete_internal_sync_meeting)
    assert callable(ard_workflow_service.assign_ard_project_owner)
    assert callable(ard_workflow_service.select_ard_team)
    assert callable(ard_workflow_service.submit_progress_review_outcome)
    assert callable(ard_workflow_service.submit_scmdp)


def test_ard_flowchart_definition_contains_actionable_transition_labels():
    definition = ard_workflow_service.get_ard_flowchart_definition()
    labels = {node["id"]: node["label"] for node in definition["nodes"]}

    assert labels[ard_workflow_service.ARD_NODE_INTERNAL_SYNC] == "Internal ARD Sync Meeting"
    assert labels[ard_workflow_service.ARD_NODE_OWNER_ASSIGNMENT] == "ARD Project Owner Assignment"
    assert labels[ard_workflow_service.ARD_NODE_TEAM_SELECTION] == "ARD Team Selection"
    assert labels[ard_workflow_service.ARD_NODE_PROGRESS_REVIEW] == "Progress Review Meeting"
    assert labels[ard_workflow_service.ARD_NODE_SCMDP_SUBMISSION] == "SCMDP Submission"


def test_ard_web_api_exposes_workspace_and_mutation_methods():
    source = Path("apps/bedo_platform/bedo_platform/api/web.py").read_text(encoding="utf-8")

    assert "get_ard_workspace" in source
    assert "schedule_ard_internal_sync_meeting" in source
    assert "complete_ard_internal_sync_meeting" in source
    assert "assign_ard_project_owner" in source
    assert "select_ard_team" in source
    assert "submit_ard_progress_review_outcome" in source
    assert "submit_ard_scmdp" in source
