from types import SimpleNamespace

from bedo_platform.constants import (
    SRS_NODE_BMDP,
    SRS_NODE_COORDINATION,
    SRS_NODE_DELIVERABLES,
    SRS_NODE_GATEWAY,
)
from bedo_platform.services import project_service


def test_command_center_can_view_all_projects_without_frappe_lookup(monkeypatch):
    monkeypatch.setattr(project_service, "_is_gm", lambda user: False)
    monkeypatch.setattr(project_service, "_is_global_viewer", lambda user: False)
    monkeypatch.setattr(project_service, "_is_command_center_representative", lambda user: True)

    assert project_service.can_view_project("commandcenter@bedo.local", "ANY-PROJECT") is True


def test_command_center_cannot_open_srs_flowchart_nodes(monkeypatch):
    monkeypatch.setattr(project_service, "_is_srs_manager", lambda user: False)
    monkeypatch.setattr(project_service, "_is_command_center_representative", lambda user: True)
    monkeypatch.setattr(project_service, "_is_selected_srs_team_member", lambda workflow, user: False)
    workflow = SimpleNamespace(project_owner="srsmanager@bedo.local")

    assert project_service._can_user_open_node("commandcenter@bedo.local", workflow, SRS_NODE_GATEWAY) is False
    assert project_service._can_user_open_node("commandcenter@bedo.local", workflow, SRS_NODE_COORDINATION) is False
    assert project_service._can_user_open_node("commandcenter@bedo.local", workflow, SRS_NODE_DELIVERABLES) is False
    assert project_service._can_user_open_node("commandcenter@bedo.local", workflow, SRS_NODE_BMDP) is False
