import pytest
from pathlib import Path
from types import SimpleNamespace

from bedo_platform.services import project_service


def test_command_center_case_3_does_not_require_deadline():
    command_case, deadline = project_service._command_center_case_and_deadline(
        {"command_center_case": project_service.COMMAND_CENTER_CASE_3}
    )

    assert command_case == project_service.COMMAND_CENTER_CASE_3
    assert deadline == 0


def test_command_center_case_1_requires_positive_deadline():
    with pytest.raises(ValueError, match="Deadline is required"):
        project_service._command_center_case_and_deadline({"command_center_case": project_service.COMMAND_CENTER_CASE_1})

    command_case, deadline = project_service._command_center_case_and_deadline(
        {"command_center_case": project_service.COMMAND_CENTER_CASE_1, "deadline_days": "3"}
    )

    assert command_case == project_service.COMMAND_CENTER_CASE_1
    assert deadline == 3


def test_command_center_case_2_requires_positive_deadline():
    with pytest.raises(ValueError, match="Deadline must be greater than zero"):
        project_service._command_center_case_and_deadline(
            {"command_center_case": project_service.COMMAND_CENTER_CASE_2, "deadline_days": "0"}
        )


def test_case3_gm_approval_opens_handover_meeting_stage():
    assert (
        project_service._handoff_status_after_command_center_gm_approval(project_service.COMMAND_CENTER_CASE_3)
        == project_service.COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_PENDING
    )
    assert (
        project_service._handoff_status_after_command_center_gm_approval(project_service.COMMAND_CENTER_CASE_1)
        == project_service.COMMAND_CENTER_HANDOFF_IN_PROGRESS
    )
    assert (
        project_service._handoff_status_after_command_center_gm_approval(project_service.COMMAND_CENTER_CASE_2)
        == project_service.COMMAND_CENTER_HANDOFF_ROUTED_TO_SUPPLIERS
    )


def test_command_center_handoff_schema_has_case3_meeting_and_confirmation_fields():
    source = Path(
        "apps/bedo_platform/bedo_platform/command_center/doctype/bedo_command_center_handoff/bedo_command_center_handoff.json"
    ).read_text(encoding="utf-8")

    assert "HANDOVER_MEETING_PENDING" in source
    assert "HANDOVER_MEETING_SCHEDULED" in source
    assert "HANDOVER_CONFIRMATION_PENDING" in source
    assert "HANDOVER_FAILED_WAITING_GM" in source
    assert '"handover_meeting"' in source
    assert '"case3_cleared_at"' in source
    assert '"handover_confirmation_status"' in source
    assert '"handover_failure_description"' in source


def test_safe_command_center_handoff_exposes_case3_meeting_state(monkeypatch):
    monkeypatch.setattr(project_service, "_safe_deadline", lambda deadline: {})
    monkeypatch.setattr(project_service, "_user_full_name", lambda user: f"Name {user}" if user else "")
    monkeypatch.setattr(project_service, "_is_command_center_representative", lambda actor: True)

    handoff = SimpleNamespace(
        name="handoff-1",
        project="project-1",
        trainer_item="trainer-1",
        srs_workflow_instance="workflow-1",
        handoff_type="SRS_TO_ARD",
        status=project_service.COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_PENDING,
        command_center_case=project_service.COMMAND_CENTER_CASE_3,
        deadline_days=0,
        approved_deadline_days=0,
        deadline="",
        responsible_user="commandcenter",
        submitted_by="commandcenter",
        submitted_at=None,
        gm_approval="approval-1",
        gm_approved_by="gm",
        gm_approved_at=None,
        completed_by="",
        completed_at=None,
        notes="",
        handover_meeting="meeting-1",
        case3_cleared_at=None,
        handover_confirmation_status="NOT_STARTED",
        handover_confirmed_by="",
        handover_confirmed_at=None,
        handover_failure_description="",
        handover_failed_by="",
        handover_failed_at=None,
    )

    row = project_service._safe_command_center_handoff(handoff, "commandcenter")

    assert row["handover_meeting"] == "meeting-1"
    assert row["handover_confirmation_status"] == "NOT_STARTED"
    assert row["can_schedule_handover_meeting"] is True
    assert row["can_submit_handover_confirmation"] is False
