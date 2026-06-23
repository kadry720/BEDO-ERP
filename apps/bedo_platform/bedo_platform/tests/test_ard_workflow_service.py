import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from bedo_platform.services import project_service
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


def test_ard_manager_can_see_every_project_and_trainer_assigned_to_ard(monkeypatch):
    class FakeFrappe:
        @staticmethod
        def get_roles(user):
            return ["ARD Manager"] if user == "ardmanager" else []

        @staticmethod
        def get_all(doctype, filters=None, fields=None, pluck=None, **_kwargs):
            assert doctype == "ARD Workflow Instance"
            assert filters == {"is_superseded": 0}
            if pluck == "trainer_item":
                return ["TRAINER-1", "TRAINER-2"]
            return [
                SimpleNamespace(project="PROJECT-1", trainer_item="TRAINER-1"),
                SimpleNamespace(project="PROJECT-2", trainer_item="TRAINER-2"),
            ]

    monkeypatch.setitem(sys.modules, "frappe", FakeFrappe)

    assert ard_workflow_service.ard_visible_project_names("ardmanager") == ["PROJECT-1", "PROJECT-2"]
    assert ard_workflow_service.ard_visible_trainer_item_names("ardmanager") == ["TRAINER-1", "TRAINER-2"]


def test_ard_non_manager_visibility_is_limited_to_active_team_memberships(monkeypatch):
    class FakeFrappe:
        @staticmethod
        def get_roles(user):
            return ["ARD Engineer"] if user == "ardengineer1" else []

        @staticmethod
        def get_all(doctype, filters=None, fields=None, pluck=None, **_kwargs):
            assert doctype == "ARD Workflow Team Member"
            assert filters == {"user": "ardengineer1", "is_active": 1}
            rows = [
                SimpleNamespace(project="PROJECT-1", trainer_item="TRAINER-1"),
                SimpleNamespace(project="PROJECT-1", trainer_item="TRAINER-1"),
            ]
            if pluck == "trainer_item":
                return [row.trainer_item for row in rows]
            return rows

    monkeypatch.setitem(sys.modules, "frappe", FakeFrappe)

    assert ard_workflow_service.ard_visible_project_names("ardengineer1") == ["PROJECT-1"]
    assert ard_workflow_service.ard_visible_trainer_item_names("ardengineer1") == ["TRAINER-1"]


def test_ard_non_manager_cannot_open_unassigned_ard_workflow(monkeypatch):
    class FakeDb:
        @staticmethod
        def exists(_doctype, _filters):
            return False

    class FakeFrappe:
        db = FakeDb()
        PermissionError = PermissionError

        @staticmethod
        def throw(message, exc):
            raise exc(message)

    monkeypatch.setitem(sys.modules, "frappe", FakeFrappe)
    monkeypatch.setattr(ard_workflow_service, "_roles", lambda _actor: {"ARD Engineer"})

    with pytest.raises(PermissionError, match="ARD workflow"):
        ard_workflow_service._assert_can_view_workflow(SimpleNamespace(name="ARD-WF-1"), "ardengineer1")


def test_ard_project_trainer_list_filters_to_visible_ard_trainers(monkeypatch):
    captured_filters = {}

    class FakeFrappe:
        @staticmethod
        def get_all(doctype, filters=None, **_kwargs):
            if doctype == "BEDO Trainer Item":
                captured_filters.update(filters or {})
            return []

    monkeypatch.setitem(sys.modules, "frappe", FakeFrappe)
    monkeypatch.setattr(project_service, "_assert_project_access", lambda _actor, _project: None)
    monkeypatch.setattr(project_service, "_is_gm", lambda _actor: False)
    monkeypatch.setattr(project_service, "_is_srs_manager", lambda _actor: False)
    monkeypatch.setattr(project_service, "_is_command_center_representative", lambda _actor: False)
    monkeypatch.setattr(project_service, "_is_ard_user", lambda _actor: True)
    monkeypatch.setattr(ard_workflow_service, "ard_visible_trainer_item_names", lambda _actor: ["TRAINER-1", "TRAINER-2"], raising=False)

    project_service.list_trainer_items_for_project("PROJECT-1", "ardmanager")

    assert captured_filters["name"] == ["in", ["TRAINER-1", "TRAINER-2"]]
