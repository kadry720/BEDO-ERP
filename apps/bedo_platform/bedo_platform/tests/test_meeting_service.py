import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from bedo_platform.services import meeting_service


CAIRO = ZoneInfo("Africa/Cairo")


def test_case3_handover_date_is_second_working_date_after_clearance():
    cleared_at = datetime(2026, 6, 21, 10, 15, tzinfo=CAIRO)

    result = meeting_service.calculate_case3_handover_date(cleared_at)

    assert result.isoformat() == "2026-06-23"


def test_case3_handover_time_must_be_at_least_second_working_date():
    cleared_at = datetime(2026, 6, 21, 10, 15, tzinfo=CAIRO)
    earliest_time = datetime(2026, 6, 23, 11, 30, tzinfo=CAIRO)
    later_time = datetime(2026, 7, 5, 11, 30, tzinfo=CAIRO)
    too_early_time = datetime(2026, 6, 22, 11, 30, tzinfo=CAIRO)

    assert meeting_service.validate_case3_handover_time(cleared_at, earliest_time) == earliest_time
    assert meeting_service.validate_case3_handover_time(cleared_at, later_time) == later_time
    with pytest.raises(ValueError, match="BMDP/PMDP release"):
        meeting_service.validate_case3_handover_time(cleared_at, too_early_time)


def test_progress_review_meeting_uses_two_complete_working_days_then_next_morning():
    completed_at = datetime(2026, 6, 21, 14, 0, tzinfo=CAIRO)

    result = meeting_service.calculate_progress_review_meeting_at(completed_at)

    assert result.isoformat() == "2026-06-24T09:00:00+03:00"


def test_meeting_reminders_are_due_once_and_skip_false_one_day_for_short_notice():
    scheduled_at = datetime(2026, 6, 23, 10, 0, tzinfo=CAIRO)
    created_at = datetime(2026, 6, 21, 9, 0, tzinfo=CAIRO)

    assert meeting_service.due_meeting_reminder_buckets(
        scheduled_at=scheduled_at,
        created_at=created_at,
        now=datetime(2026, 6, 22, 10, 0, tzinfo=CAIRO),
        one_day_sent_at=None,
        one_hour_sent_at=None,
    ) == ["one_day"]

    assert meeting_service.due_meeting_reminder_buckets(
        scheduled_at=scheduled_at,
        created_at=created_at,
        now=datetime(2026, 6, 22, 10, 5, tzinfo=CAIRO),
        one_day_sent_at=datetime(2026, 6, 22, 10, 0, tzinfo=CAIRO),
        one_hour_sent_at=None,
    ) == []

    assert meeting_service.due_meeting_reminder_buckets(
        scheduled_at=scheduled_at,
        created_at=created_at,
        now=datetime(2026, 6, 23, 9, 0, tzinfo=CAIRO),
        one_day_sent_at=datetime(2026, 6, 22, 10, 0, tzinfo=CAIRO),
        one_hour_sent_at=None,
    ) == ["one_hour"]

    short_notice_scheduled = datetime(2026, 6, 23, 10, 0, tzinfo=CAIRO)
    short_notice_created = datetime(2026, 6, 22, 18, 0, tzinfo=CAIRO)
    assert meeting_service.due_meeting_reminder_buckets(
        scheduled_at=short_notice_scheduled,
        created_at=short_notice_created,
        now=datetime(2026, 6, 23, 8, 0, tzinfo=CAIRO),
        one_day_sent_at=None,
        one_hour_sent_at=None,
    ) == []


def test_validate_department_participants_rejects_out_of_department_users():
    active_srs_users = {"srsmanager", "srselectronicshead"}

    assert meeting_service.validate_department_participants(
        ["srselectronicshead", "srsmanager", "srsmanager"],
        active_srs_users,
        department_key="SRS",
    ) == ["srselectronicshead", "srsmanager"]

    with pytest.raises(ValueError, match="SRS"):
        meeting_service.validate_department_participants(
            ["srselectronicshead", "ardmanager"],
            active_srs_users,
            department_key="SRS",
        )


def test_case3_handover_meeting_ids_are_stable_per_handoff_generation():
    assert meeting_service.case3_handover_meeting_id("handoff-1", 3) == "CASE3-HANDOVER-handoff-1-G3"


def test_required_meeting_leads_confirmed_requires_every_required_lead():
    assert meeting_service.required_meeting_leads_confirmed(
        [
            SimpleNamespace(is_required=1, participation_source="required lead", confirmation_status="CONFIRMED"),
            SimpleNamespace(is_required=1, participation_source="required lead", confirmation_status="PENDING"),
            SimpleNamespace(is_required=0, participation_source="selected team member", confirmation_status="PENDING"),
        ]
    ) is False
    assert meeting_service.required_meeting_leads_confirmed(
        [
            SimpleNamespace(is_required=1, participation_source="required lead", confirmation_status="CONFIRMED"),
            SimpleNamespace(is_required=1, participation_source="required lead", confirmation_status="CONFIRMED"),
        ]
    ) is True


def test_meeting_row_includes_confirmation_candidates_for_actor(monkeypatch):
    row = SimpleNamespace(
        name="MEET-1",
        meeting_id="CASE3-HANDOVER-1",
        meeting_type="HANDOVER_MEETING",
        project="PROJ-1",
        trainer_item="ITEM-1",
        source_workflow="WF-1",
        source_workflow_generation=1,
        source_node="COMMAND_CENTER_CASE_3_HANDOVER_MEETING",
        organizer="commandcenter",
        organizer_department="COMMAND_CENTER",
        scheduled_at=None,
        time_zone="Africa/Cairo",
        expected_end_at=None,
        status="PENDING_CONFIRMATION",
        title="Case 3 Handover Meeting",
        description="",
        created_at=None,
        confirmed_at=None,
        completed_at=None,
        overdue_at=None,
    )
    monkeypatch.setattr(meeting_service, "_meeting_participants", lambda meeting: [])
    monkeypatch.setattr(meeting_service, "_confirmation_candidates_for_actor", lambda actor, meeting: ["srselectronicshead"])
    monkeypatch.setattr(
        meeting_service,
        "_meeting_handover_context",
        lambda meeting_row: {"project_code": "", "project_name": "", "handover_paths": []},
    )

    result = meeting_service._meeting_row(row, actor="srsmanager")

    assert result["confirmation_candidates"] == ["srselectronicshead"]


def test_meeting_row_includes_project_and_handover_paths(monkeypatch):
    row = SimpleNamespace(
        name="MEET-1",
        meeting_id="CASE3-HANDOVER-1",
        meeting_type="HANDOVER_MEETING",
        project="PROJ-1",
        trainer_item="ITEM-1",
        source_workflow="WF-1",
        source_workflow_generation=1,
        source_node="COMMAND_CENTER_CASE_3_HANDOVER_MEETING",
        organizer="commandcenter",
        organizer_department="COMMAND_CENTER",
        scheduled_at=None,
        time_zone="Africa/Cairo",
        expected_end_at=None,
        status="PENDING_CONFIRMATION",
        title="Case 3 Handover Meeting",
        description="",
        created_at=None,
        confirmed_at=None,
        completed_at=None,
        overdue_at=None,
    )
    monkeypatch.setattr(meeting_service, "_meeting_participants", lambda meeting: [])
    monkeypatch.setattr(meeting_service, "_confirmation_candidates_for_actor", lambda actor, meeting: [])
    monkeypatch.setattr(
        meeting_service,
        "_meeting_handover_context",
        lambda meeting_row: {
            "project_code": "BEDO-001",
            "project_name": "Press Upgrade",
            "handover_paths": [
                {"label": "BMDP Path", "path": "share/bmdp.pdf"},
                {"label": "PMDP Path", "path": "share/pmdp.pdf"},
            ],
        },
        raising=False,
    )

    result = meeting_service._meeting_row(row, actor="ardmanager")

    assert result["project_code"] == "BEDO-001"
    assert result["project_name"] == "Press Upgrade"
    assert result["handover_paths"] == [
        {"label": "BMDP Path", "path": "share/bmdp.pdf"},
        {"label": "PMDP Path", "path": "share/pmdp.pdf"},
    ]


def test_list_my_meetings_only_returns_active_participant_meetings(monkeypatch):
    calls = []

    class FakeDb:
        @staticmethod
        def exists(*_args, **_kwargs):
            return True

    class FakeFrappe:
        db = FakeDb()
        PermissionError = PermissionError

        @staticmethod
        def get_roles(_user):
            return ["General Manager"]

        @staticmethod
        def get_all(doctype, filters=None, fields=None, order_by=None, page_length=None, pluck=None):
            calls.append((doctype, filters, pluck))
            if doctype == "BEDO Meeting Participant":
                assert filters == {"user": "gm", "is_active": 1}
                assert pluck == "meeting"
                return ["VISIBLE-MEETING"]
            if doctype == "BEDO Meeting":
                assert filters and filters.get("name") == ["in", ["VISIBLE-MEETING"]]
                return [SimpleNamespace(name="VISIBLE-MEETING")]
            return []

    monkeypatch.setitem(sys.modules, "frappe", FakeFrappe)
    monkeypatch.setattr(meeting_service, "_meeting_row", lambda row, actor: {"name": row.name})

    result = meeting_service.list_my_meetings("gm")

    assert result == {"meetings": [{"name": "VISIBLE-MEETING"}], "count": 1}
    assert calls[0][0] == "BEDO Meeting Participant"


def test_case3_handover_meeting_mutations_are_exposed():
    assert callable(meeting_service.schedule_case3_handover_meeting)
    assert callable(meeting_service.confirm_meeting_attendance)


def test_meeting_doctypes_and_scheduler_are_registered():
    assert Path("apps/bedo_platform/bedo_platform/bedo_core/doctype/bedo_meeting/bedo_meeting.json").exists()
    assert Path(
        "apps/bedo_platform/bedo_platform/bedo_core/doctype/bedo_meeting_participant/bedo_meeting_participant.json"
    ).exists()
    hooks = Path("apps/bedo_platform/bedo_platform/hooks.py").read_text(encoding="utf-8")

    assert "bedo_platform.services.meeting_service.run_meeting_reminders" in hooks
    assert "bedo_platform.services.meeting_service.run_meeting_auto_completion" in hooks
    assert "bedo_platform.services.meeting_service.run_meeting_overdue_check" in hooks
