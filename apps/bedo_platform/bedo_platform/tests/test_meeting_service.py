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


def test_case3_handover_time_must_be_on_fixed_second_working_date():
    cleared_at = datetime(2026, 6, 21, 10, 15, tzinfo=CAIRO)
    valid_time = datetime(2026, 6, 23, 11, 30, tzinfo=CAIRO)
    invalid_time = datetime(2026, 6, 24, 11, 30, tzinfo=CAIRO)

    assert meeting_service.validate_case3_handover_time(cleared_at, valid_time) == valid_time
    with pytest.raises(ValueError, match="second working date"):
        meeting_service.validate_case3_handover_time(cleared_at, invalid_time)


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
