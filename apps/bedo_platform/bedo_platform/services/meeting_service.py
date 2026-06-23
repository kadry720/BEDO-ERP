from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

from bedo_platform.constants import COMMAND_CENTER_ROLES, GLOBAL_VIEW_ROLES
from bedo_platform.services.deadline_service import CAIRO_TZ, WORK_START, is_working_day, to_cairo_iso, to_storage_datetime
from bedo_platform.services.security_audit_service import log_security_event
from bedo_platform.services.user_profile_service import assert_user_can_login

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


def case3_handover_meeting_id(handoff_name: str, generation: int | str | None = 1) -> str:
    return f"CASE3-HANDOVER-{handoff_name}-G{int(generation or 1)}"


def required_meeting_leads_confirmed(participants: Iterable[object]) -> bool:
    required = [
        row
        for row in participants
        if int(getattr(row, "is_required", 0) or 0)
        and getattr(row, "participation_source", "") == "required lead"
    ]
    return bool(required) and all(getattr(row, "confirmation_status", "") == "CONFIRMED" for row in required)


def _roles(user: str) -> set[str]:
    import frappe

    return set(frappe.get_roles(user))


def _is_global_viewer(user: str) -> bool:
    return bool(_roles(user) & GLOBAL_VIEW_ROLES)


def _primary_department_key(user: str) -> str:
    import frappe

    department = frappe.db.get_value(
        "BEDO User Role Assignment",
        {"user": user, "is_primary_department": 1, "is_active": 1},
        "department",
    )
    if not department:
        return ""
    return frappe.db.get_value("BEDO Department", department, "department_key") or ""


def _active_users_with_role(role: str) -> list[str]:
    import frappe

    users = []
    for row in frappe.get_all("Has Role", filters={"role": role}, fields=["parent"]):
        if row.parent not in {"Administrator", "Guest"} and assert_user_can_login(row.parent):
            users.append(row.parent)
    return sorted(set(users))


def _active_users_in_department(department_key: str) -> list[str]:
    import frappe

    users = []
    for row in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]):
        if row.name in {"Administrator", "Guest"} or not assert_user_can_login(row.name):
            continue
        if _primary_department_key(row.name) == department_key:
            users.append(row.name)
    return sorted(set(users))


def _meeting_actor_department(actor: str) -> str:
    roles = _roles(actor)
    if "SRS Manager" in roles:
        return "SRS"
    if "ARD Manager" in roles:
        return "ARD"
    if roles & COMMAND_CENTER_ROLES:
        return "COMMAND_CENTER"
    return _primary_department_key(actor)


def _upsert_meeting_participant(
    *,
    meeting: str,
    user: str,
    department: str,
    participation_source: str,
    selected_by: str,
    is_required: int = 0,
    confirmation_status: str = "PENDING",
) -> str:
    import frappe

    existing = frappe.db.get_value("BEDO Meeting Participant", {"meeting": meeting, "user": user}, "name")
    doc = frappe.get_doc("BEDO Meeting Participant", existing) if existing else frappe.new_doc("BEDO Meeting Participant")
    doc.meeting = meeting
    doc.user = user
    doc.department = department
    doc.participation_source = participation_source
    doc.selected_by = selected_by
    doc.is_required = is_required
    doc.confirmation_status = doc.confirmation_status or confirmation_status
    doc.is_active = 1
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    return doc.name


def schedule_case3_handover_meeting(
    *,
    handoff,
    scheduled_at: datetime,
    actor: str,
    command_center_colleagues: Iterable[str] | None = None,
) -> dict[str, object]:
    import frappe
    from bedo_platform.services.notification_service import notify_many

    cleared_at = getattr(handoff, "case3_cleared_at", None) or getattr(handoff, "gm_approved_at", None) or datetime.now(CAIRO_TZ)
    scheduled = validate_case3_handover_time(cleared_at, scheduled_at)
    generation = int(getattr(handoff, "generation", 1) or 1)
    meeting_id = case3_handover_meeting_id(handoff.name, generation)
    existing = frappe.db.get_value("BEDO Meeting", {"meeting_id": meeting_id, "is_superseded": 0}, "name")
    meeting = frappe.get_doc("BEDO Meeting", existing) if existing else frappe.new_doc("BEDO Meeting")
    meeting.meeting_id = meeting_id
    meeting.meeting_type = MEETING_TYPE_HANDOVER
    meeting.project = handoff.project
    meeting.trainer_item = handoff.trainer_item
    meeting.source_workflow = handoff.srs_workflow_instance
    meeting.source_workflow_generation = generation
    meeting.source_node = "COMMAND_CENTER_CASE_3_HANDOVER_MEETING"
    meeting.organizer = actor
    meeting.organizer_department = "COMMAND_CENTER"
    meeting.scheduled_at = to_storage_datetime(scheduled)
    meeting.time_zone = "Africa/Cairo"
    meeting.expected_end_at = to_storage_datetime(scheduled + STANDARD_MEETING_DURATION)
    meeting.status = MEETING_STATUS_PENDING_CONFIRMATION
    meeting.title = "Case 3 Handover Meeting"
    meeting.description = getattr(handoff, "notes", "") or "Command Center Case 3 SRS to ARD handover."
    meeting.created_at = getattr(meeting, "created_at", None) or to_storage_datetime(datetime.now(CAIRO_TZ))
    meeting.related_reference_doctype = "BEDO Command Center Handoff"
    meeting.related_reference_name = handoff.name
    meeting.is_superseded = 0
    meeting.flags.ignore_permissions = True
    if existing:
        meeting.save(ignore_permissions=True)
    else:
        meeting.insert(ignore_permissions=True)

    _upsert_meeting_participant(
        meeting=meeting.name,
        user=actor,
        department="COMMAND_CENTER",
        participation_source="organizer",
        selected_by=actor,
        confirmation_status="CONFIRMED",
    )
    colleagues = validate_department_participants(
        command_center_colleagues or [],
        _active_users_in_department("COMMAND_CENTER"),
        department_key="COMMAND_CENTER",
    )
    for user in colleagues:
        _upsert_meeting_participant(
            meeting=meeting.name,
            user=user,
            department="COMMAND_CENTER",
            participation_source="selected colleague",
            selected_by=actor,
        )
    for user in _active_users_with_role("SRS Manager"):
        _upsert_meeting_participant(
            meeting=meeting.name,
            user=user,
            department="SRS",
            participation_source="required lead",
            selected_by=actor,
            is_required=1,
        )
    for user in _active_users_with_role("ARD Manager"):
        _upsert_meeting_participant(
            meeting=meeting.name,
            user=user,
            department="ARD",
            participation_source="required lead",
            selected_by=actor,
            is_required=1,
        )
    recipients = _participant_users(meeting.name)
    if recipients:
        notify_many(
            recipients,
            title="Case 3 Handover Meeting",
            message=f"Case 3 Handover Meeting is scheduled for {to_cairo_iso(meeting.scheduled_at)}.",
            notification_type="MEETING_INVITATION",
            project=handoff.project,
            trainer_item=handoff.trainer_item,
            workflow_type=MEETING_TYPE_HANDOVER,
            node_id="COMMAND_CENTER_CASE_3_HANDOVER_MEETING",
            action_url="/meetings",
            priority="High",
        )
    log_security_event(
        "handover_meeting_scheduled",
        user=actor,
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        workflow_type=MEETING_TYPE_HANDOVER,
        node_id="COMMAND_CENTER_CASE_3_HANDOVER_MEETING",
        status="Success",
        message=meeting_id,
    )
    return {"meeting": meeting.name, "meeting_id": meeting_id, "scheduled_at": to_cairo_iso(meeting.scheduled_at)}


def confirm_meeting_attendance(meeting: str, selected_users: Iterable[str], actor: str) -> dict[str, object]:
    import frappe

    if not frappe.db.exists("BEDO Meeting", meeting):
        frappe.throw("Meeting not found.", frappe.DoesNotExistError)
    meeting_doc = frappe.get_doc("BEDO Meeting", meeting)
    if meeting_doc.is_superseded or meeting_doc.status in {MEETING_STATUS_CANCELLED, MEETING_STATUS_SUPERSEDED_BY_RESET}:
        frappe.throw("Meeting is no longer active.", frappe.PermissionError)
    participant_name = frappe.db.get_value(
        "BEDO Meeting Participant",
        {"meeting": meeting, "user": actor, "is_active": 1},
        "name",
    )
    if not participant_name:
        frappe.throw("Only active meeting participants can confirm attendance.", frappe.PermissionError)
    department = _meeting_actor_department(actor)
    if department not in {"SRS", "ARD", "COMMAND_CENTER"}:
        frappe.throw("Meeting confirmation is not available for this department.", frappe.PermissionError)

    selected = validate_department_participants(
        selected_users,
        _active_users_in_department(department),
        department_key=department,
    )
    source = "selected colleague" if department == "COMMAND_CENTER" else "selected team member"
    for user in selected:
        _upsert_meeting_participant(
            meeting=meeting,
            user=user,
            department=department,
            participation_source=source,
            selected_by=actor,
        )

    now = datetime.now(CAIRO_TZ)
    participant = frappe.get_doc("BEDO Meeting Participant", participant_name)
    participant.confirmation_status = "CONFIRMED"
    participant.confirmed_at = to_storage_datetime(now)
    participant.flags.ignore_permissions = True
    participant.save(ignore_permissions=True)

    participants = frappe.get_all(
        "BEDO Meeting Participant",
        filters={"meeting": meeting, "is_active": 1},
        fields=["is_required", "participation_source", "confirmation_status"],
    )
    all_required_confirmed = required_meeting_leads_confirmed(participants)
    if all_required_confirmed:
        meeting_doc.status = MEETING_STATUS_CONFIRMED
        meeting_doc.confirmed_at = to_storage_datetime(now)
        meeting_doc.flags.ignore_permissions = True
        meeting_doc.save(ignore_permissions=True)
    log_security_event(
        "meeting_attendance_confirmed",
        user=actor,
        project=meeting_doc.project,
        trainer_item=meeting_doc.trainer_item,
        workflow_type=meeting_doc.meeting_type,
        node_id=meeting_doc.source_node,
        status="Success",
        message=f"Selected {len(selected)} participant(s)",
    )
    return {"success": True, "meeting": meeting, "all_required_confirmed": all_required_confirmed}


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
