from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

from bedo_platform.constants import GLOBAL_VIEW_ROLES
from bedo_platform.services.deadline_service import CAIRO_TZ, WORK_START, is_working_day, to_cairo_iso, to_storage_datetime

MEETING_STATUS_DRAFT = "DRAFT"
MEETING_STATUS_PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
MEETING_STATUS_CONFIRMED = "CONFIRMED"
MEETING_STATUS_SCHEDULED = "SCHEDULED"
MEETING_STATUS_COMPLETED = "COMPLETED"
MEETING_STATUS_OVERDUE = "OVERDUE"
MEETING_STATUS_CANCELLED = "CANCELLED"
MEETING_STATUS_SUPERSEDED_BY_RESET = "SUPERSEDED_BY_RESET"

MEETING_TYPE_HANDOVER = "HANDOVER_MEETING"
MEETING_TYPE_INTERNAL_ARD_SYNC = "INTERNAL_ARD_SYNC_MEETING"
MEETING_TYPE_PROGRESS_REVIEW = "PROGRESS_REVIEW_MEETING"
STANDARD_MEETING_DURATION = timedelta(hours=1)


def _as_cairo(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=CAIRO_TZ)
    return value.astimezone(CAIRO_TZ)


def _next_working_date_after(value: date) -> date:
    candidate = datetime.combine(value + timedelta(days=1), WORK_START, tzinfo=CAIRO_TZ)
    while not is_working_day(candidate):
        candidate += timedelta(days=1)
    return candidate.date()


def _nth_working_date_after(value: datetime, count: int) -> date:
    if count < 1:
        raise ValueError("Working date count must be at least 1.")
    current_date = _as_cairo(value).date()
    for _index in range(count):
        current_date = _next_working_date_after(current_date)
    return current_date


def calculate_case3_handover_date(cleared_at: datetime) -> date:
    return _nth_working_date_after(cleared_at, 2)


def validate_case3_handover_time(cleared_at: datetime, scheduled_at: datetime) -> datetime:
    scheduled = _as_cairo(scheduled_at)
    expected_date = calculate_case3_handover_date(cleared_at)
    if scheduled.date() != expected_date:
        raise ValueError("Case 3 Handover Meeting must be scheduled on the second working date after clearance.")
    return scheduled


def calculate_progress_review_meeting_at(team_selection_completed_at: datetime) -> datetime:
    second_full_working_date = _nth_working_date_after(team_selection_completed_at, 2)
    meeting_date = _next_working_date_after(second_full_working_date)
    return datetime.combine(meeting_date, WORK_START, tzinfo=CAIRO_TZ)


def due_meeting_reminder_buckets(
    *,
    scheduled_at: datetime,
    created_at: datetime,
    now: datetime,
    one_day_sent_at: datetime | None,
    one_hour_sent_at: datetime | None,
) -> list[str]:
    scheduled = _as_cairo(scheduled_at)
    created = _as_cairo(created_at)
    current = _as_cairo(now)
    if current >= scheduled:
        return []

    due: list[str] = []
    notice = scheduled - current
    was_created_with_one_day_notice = scheduled - created >= timedelta(hours=24)
    if one_day_sent_at is None and was_created_with_one_day_notice and notice <= timedelta(hours=24):
        due.append("one_day")
    if one_hour_sent_at is None and notice <= timedelta(hours=1):
        due.append("one_hour")
    return due


def validate_department_participants(
    selected_users: Iterable[str],
    active_department_users: Iterable[str],
    *,
    department_key: str,
) -> list[str]:
    allowed = {str(user) for user in active_department_users if str(user or "").strip()}
    selected = sorted({str(user) for user in selected_users if str(user or "").strip()})
    invalid = [user for user in selected if user not in allowed]
    if invalid:
        raise ValueError(f"Only active {department_key} department users may be selected: {', '.join(invalid)}")
    return selected


def _roles(user: str) -> set[str]:
    import frappe

    return set(frappe.get_roles(user))


def _is_global_viewer(user: str) -> bool:
    return bool(_roles(user) & GLOBAL_VIEW_ROLES)


def _meeting_participants(meeting: str) -> list[dict[str, object]]:
    import frappe

    rows = frappe.get_all(
        "BEDO Meeting Participant",
        filters={"meeting": meeting, "is_active": 1},
        fields=[
            "user",
            "department",
            "participation_source",
            "selected_by",
            "is_required",
            "confirmation_status",
            "confirmed_at",
        ],
        order_by="creation asc",
    )
    return [
        {
            **dict(row),
            "confirmed_at": to_cairo_iso(row.confirmed_at),
        }
        for row in rows
    ]


def _meeting_row(row) -> dict[str, object]:
    return {
        "name": row.name,
        "meeting_id": row.meeting_id,
        "meeting_type": row.meeting_type,
        "project": row.project,
        "trainer_item": row.trainer_item,
        "source_workflow": row.source_workflow,
        "source_workflow_generation": row.source_workflow_generation,
        "source_node": row.source_node,
        "organizer": row.organizer,
        "organizer_department": row.organizer_department,
        "scheduled_at": to_cairo_iso(row.scheduled_at),
        "time_zone": row.time_zone,
        "expected_end_at": to_cairo_iso(row.expected_end_at),
        "status": row.status,
        "title": row.title,
        "description": row.description,
        "created_at": to_cairo_iso(row.created_at),
        "confirmed_at": to_cairo_iso(row.confirmed_at),
        "completed_at": to_cairo_iso(row.completed_at),
        "overdue_at": to_cairo_iso(row.overdue_at),
        "participants": _meeting_participants(row.name),
    }


def list_my_meetings(actor: str, *, status: str = "") -> dict[str, object]:
    import frappe

    filters: dict[str, object] = {"is_superseded": 0}
    if status:
        filters["status"] = status
    if _is_global_viewer(actor) or "General Manager" in _roles(actor):
        meeting_names = None
    else:
        meeting_names = frappe.get_all(
            "BEDO Meeting Participant",
            filters={"user": actor, "is_active": 1},
            pluck="meeting",
        )
        if not meeting_names:
            return {"meetings": [], "count": 0}
        filters["name"] = ["in", sorted(set(meeting_names))]
    rows = frappe.get_all(
        "BEDO Meeting",
        filters=filters,
        fields=[
            "name",
            "meeting_id",
            "meeting_type",
            "project",
            "trainer_item",
            "source_workflow",
            "source_workflow_generation",
            "source_node",
            "organizer",
            "organizer_department",
            "scheduled_at",
            "time_zone",
            "expected_end_at",
            "status",
            "title",
            "description",
            "created_at",
            "confirmed_at",
            "completed_at",
            "overdue_at",
        ],
        order_by="scheduled_at asc",
        page_length=100,
    )
    meetings = [_meeting_row(row) for row in rows]
    return {"meetings": meetings, "count": len(meetings)}


def _participant_users(meeting: str) -> list[str]:
    import frappe

    return sorted(
        set(
            frappe.get_all(
                "BEDO Meeting Participant",
                filters={"meeting": meeting, "is_active": 1},
                pluck="user",
            )
        )
    )


def run_meeting_reminders() -> dict[str, int]:
    import frappe
    from bedo_platform.services.notification_service import notify_many

    now = datetime.now(CAIRO_TZ)
    checked = 0
    sent = 0
    rows = frappe.get_all(
        "BEDO Meeting",
        filters={
            "status": ["in", [MEETING_STATUS_PENDING_CONFIRMATION, MEETING_STATUS_CONFIRMED, MEETING_STATUS_SCHEDULED]],
            "is_superseded": 0,
        },
        fields=[
            "name",
            "project",
            "trainer_item",
            "meeting_type",
            "title",
            "scheduled_at",
            "created_at",
            "one_day_reminder_sent_at",
            "one_hour_reminder_sent_at",
        ],
        page_length=500,
    )
    for row in rows:
        checked += 1
        buckets = due_meeting_reminder_buckets(
            scheduled_at=row.scheduled_at,
            created_at=row.created_at,
            now=now,
            one_day_sent_at=row.one_day_reminder_sent_at,
            one_hour_sent_at=row.one_hour_reminder_sent_at,
        )
        if not buckets:
            continue
        recipients = _participant_users(row.name)
        if not recipients:
            continue
        for bucket in buckets:
            notify_many(
                recipients,
                title=f"{row.title} reminder",
                message=f"{row.title} is scheduled for {to_cairo_iso(row.scheduled_at)}.",
                notification_type="MEETING_REMINDER_ONE_DAY" if bucket == "one_day" else "MEETING_REMINDER_ONE_HOUR",
                project=row.project,
                trainer_item=row.trainer_item,
                workflow_type=row.meeting_type,
                action_url="/meetings",
                priority="High",
            )
            fieldname = "one_day_reminder_sent_at" if bucket == "one_day" else "one_hour_reminder_sent_at"
            frappe.db.set_value("BEDO Meeting", row.name, fieldname, to_storage_datetime(now), update_modified=False)
            sent += len(recipients)
    return {"checked": checked, "sent": sent}


def run_meeting_auto_completion() -> dict[str, int]:
    import frappe

    now = datetime.now(CAIRO_TZ)
    checked = 0
    completed = 0
    rows = frappe.get_all(
        "BEDO Meeting",
        filters={
            "status": ["in", [MEETING_STATUS_CONFIRMED, MEETING_STATUS_SCHEDULED]],
            "is_superseded": 0,
            "expected_end_at": ["<=", to_storage_datetime(now)],
            "meeting_type": ["!=", MEETING_TYPE_HANDOVER],
        },
        fields=["name", "expected_end_at"],
        page_length=500,
    )
    for row in rows:
        checked += 1
        frappe.db.set_value(
            "BEDO Meeting",
            row.name,
            {"status": MEETING_STATUS_COMPLETED, "completed_at": to_storage_datetime(now)},
            update_modified=False,
        )
        completed += 1
    return {"checked": checked, "completed": completed}


def run_meeting_overdue_check() -> dict[str, int]:
    import frappe
    from bedo_platform.services.notification_service import notify_many
    from bedo_platform.services.project_service import _active_users_with_role

    now = datetime.now(CAIRO_TZ)
    checked = 0
    marked = 0
    sent = 0
    rows = frappe.get_all(
        "BEDO Meeting",
        filters={
            "status": ["in", [MEETING_STATUS_PENDING_CONFIRMATION, MEETING_STATUS_CONFIRMED, MEETING_STATUS_SCHEDULED]],
            "is_superseded": 0,
            "expected_end_at": ["<=", to_storage_datetime(now)],
            "overdue_at": ["is", "not set"],
        },
        fields=["name", "project", "trainer_item", "meeting_type", "title", "expected_end_at", "organizer"],
        page_length=500,
    )
    for row in rows:
        checked += 1
        recipients = set(_participant_users(row.name))
        recipients.update(_active_users_with_role("General Manager"))
        if row.organizer:
            recipients.add(row.organizer)
        if recipients:
            notify_many(
                sorted(recipients),
                title=f"{row.title} overdue",
                message=f"{row.title} is overdue. Expected end: {to_cairo_iso(row.expected_end_at)}.",
                notification_type="MEETING_OVERDUE",
                project=row.project,
                trainer_item=row.trainer_item,
                workflow_type=row.meeting_type,
                action_url="/meetings",
                priority="High",
            )
            sent += len(recipients)
        frappe.db.set_value(
            "BEDO Meeting",
            row.name,
            {"status": MEETING_STATUS_OVERDUE, "overdue_at": to_storage_datetime(now)},
            update_modified=False,
        )
        marked += 1
    return {"checked": checked, "overdue": marked, "sent": sent}
