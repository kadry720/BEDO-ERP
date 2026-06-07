from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

CAIRO_TZ = ZoneInfo("Africa/Cairo")
WORKING_WEEKDAYS = {6, 0, 1, 2, 3}
WORK_START = time(9, 0)
WORK_END = time(17, 0)


def _as_cairo(value: datetime | None = None) -> datetime:
    value = value or datetime.now(CAIRO_TZ)
    if value.tzinfo is None:
        return value.replace(tzinfo=CAIRO_TZ)
    return value.astimezone(CAIRO_TZ)


def is_working_day(value: datetime) -> bool:
    return _as_cairo(value).weekday() in WORKING_WEEKDAYS


def calculate_next_working_start(triggered_at: datetime | None = None) -> datetime:
    current = _as_cairo(triggered_at)
    candidate = datetime.combine(current.date() + timedelta(days=1), WORK_START, tzinfo=CAIRO_TZ)
    while not is_working_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def calculate_working_due_at(start_at: datetime, deadline_days: int) -> datetime:
    if int(deadline_days) < 1:
        raise ValueError("Deadline days must be at least 1.")
    due_day = _as_cairo(start_at)
    remaining = int(deadline_days) - 1
    while remaining:
        due_day += timedelta(days=1)
        if is_working_day(due_day):
            remaining -= 1
    return datetime.combine(due_day.date(), WORK_END, tzinfo=CAIRO_TZ)


def to_storage_datetime(value: datetime) -> datetime:
    return _as_cairo(value).replace(tzinfo=None)


def to_cairo_iso(value: datetime | str | None) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return value
        return _as_cairo(parsed).isoformat()
    return _as_cairo(value).isoformat()


def server_now_iso() -> str:
    return datetime.now(CAIRO_TZ).isoformat()


def _deadline_status(row) -> str:
    if row.status != "ACTIVE":
        return row.status
    due_at = _as_cairo(row.due_at)
    if datetime.now(CAIRO_TZ) > due_at:
        return "OVERDUE"
    return "ACTIVE"


def create_deadline(
    *,
    project: str,
    trainer_item: str,
    workflow_type: str,
    node_id: str,
    triggered_by: str,
    deadline_days: int,
    triggered_at: datetime | None = None,
) -> dict[str, object]:
    import frappe

    triggered = _as_cairo(triggered_at)
    start = calculate_next_working_start(triggered)
    due = calculate_working_due_at(start, deadline_days)
    doc = frappe.get_doc(
        {
            "doctype": "BEDO Deadline",
            "project": project,
            "trainer_item": trainer_item,
            "workflow_type": workflow_type,
            "node_id": node_id,
            "triggered_by": triggered_by,
            "triggered_at": to_storage_datetime(triggered),
            "start_at": to_storage_datetime(start),
            "due_at": to_storage_datetime(due),
            "deadline_days": int(deadline_days),
            "status": "ACTIVE",
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    return {"name": doc.name, "start_at": doc.start_at, "due_at": doc.due_at, "deadline_days": doc.deadline_days}


def complete_deadlines(trainer_item: str, node_id: str) -> None:
    import frappe

    for name in frappe.get_all(
        "BEDO Deadline",
        filters={"trainer_item": trainer_item, "node_id": node_id, "status": "ACTIVE"},
        pluck="name",
    ):
        frappe.db.set_value("BEDO Deadline", name, "status", "COMPLETED", update_modified=False)


def get_deadlines_for_trainer_item(trainer_item: str) -> list[dict[str, object]]:
    import frappe

    rows = frappe.get_all(
        "BEDO Deadline",
        filters={"trainer_item": trainer_item},
        fields=["name", "workflow_type", "node_id", "start_at", "due_at", "deadline_days", "status", "reminder_notified_at", "overdue_notified_at"],
        order_by="due_at asc",
    )
    now = server_now_iso()
    return [
        {
            **dict(row),
            "start_at": to_cairo_iso(row.start_at),
            "due_at": to_cairo_iso(row.due_at),
            "deadline_status": _deadline_status(row),
            "server_now": now,
        }
        for row in rows
    ]


def run_deadline_reminder_check() -> dict[str, int]:
    return {"checked": 0, "sent": 0}


def run_overdue_check() -> dict[str, int]:
    return {"checked": 0, "sent": 0}
