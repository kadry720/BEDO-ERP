from __future__ import annotations

import os
from datetime import datetime, time, timedelta
from math import ceil
from zoneinfo import ZoneInfo

from bedo_platform.constants import GLOBAL_DEADLINE_EXTENSION_APPROVAL
from bedo_platform.services.notification_service import project_action_url

CAIRO_TZ = ZoneInfo("Africa/Cairo")
WORKING_WEEKDAYS = {6, 0, 1, 2, 3}
WORK_START = time(9, 0)
WORK_END = time(17, 0)
DEADLINE_MODE_ENV = "BEDO_SRS_DEADLINE_MODE"
DEADLINE_MODE_WORKING_DAYS = "working_days"
DEADLINE_MODE_MINUTES = "minutes"
NODE_LABELS = {
    "PRODUCT_DIGITAL_RELEASE": "Product Digital Release",
    "SRS_GATEWAY": "SRS Gateway",
    "MANDATORY_COORDINATION_MEETING": "Mandatory Coordination Meeting",
    "DELIVERABLES_MATRIX": "Deliverables Submission",
    "DUAL_GATE_APPROVAL": "Dual Gate Approval",
    "DEADLINE_LOCKED_IN_ERP": "Deadline Locked in ERP",
    "ACTION_PATHS": "Action Paths",
    "CASE_1": "Case 1",
    "CASE_2": "Case 2",
    "CASE_3": "Case 3",
    "CASE_4": "Case 4",
    "GATE_2_PMDP": "Gate 2 PMDP",
    "PMDP_DUAL_GATE_APPROVAL": "PMDP Dual Gate Approval",
    "PHYSICAL_BUILD_TEST": "Physical Build & Test",
    "EXTENSION_DEADLINE": "Extension Deadline",
    "SRS_DIRECTOR_APPROVAL": "SRS Director Approval",
    "PMDP": "PMDP",
    "BMDP": "BMDP",
    "COMMAND_CENTER_APPROVAL": "Command Center Approval",
    "FINAL_GM_APPROVAL": "Final GM Approval",
}


def deadline_mode() -> str:
    configured = os.environ.get(DEADLINE_MODE_ENV, DEADLINE_MODE_WORKING_DAYS).strip().lower()
    return DEADLINE_MODE_WORKING_DAYS if configured == DEADLINE_MODE_WORKING_DAYS else DEADLINE_MODE_MINUTES


def using_minute_deadlines() -> bool:
    return deadline_mode() == DEADLINE_MODE_MINUTES


def deadline_unit_label(quantity: int | None = None) -> str:
    singular = "minute" if using_minute_deadlines() else "working day"
    if quantity == 1:
        return singular
    return f"{singular}s"


def deadline_quantity_label(quantity: int | str | None) -> str:
    if quantity in (None, ""):
        return ""
    amount = int(quantity)
    return f"{amount} {deadline_unit_label(amount)}"


def _as_cairo(value: datetime | None = None) -> datetime:
    value = value or datetime.now(CAIRO_TZ)
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        return value.replace(tzinfo=CAIRO_TZ)
    return value.astimezone(CAIRO_TZ)


def is_working_day(value: datetime) -> bool:
    return _as_cairo(value).weekday() in WORKING_WEEKDAYS


def calculate_next_working_start(triggered_at: datetime | None = None) -> datetime:
    current = _as_cairo(triggered_at)
    if using_minute_deadlines():
        return current
    candidate = datetime.combine(current.date() + timedelta(days=1), WORK_START, tzinfo=CAIRO_TZ)
    while not is_working_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def calculate_working_due_at(start_at: datetime, deadline_days: int) -> datetime:
    if int(deadline_days) < 1:
        raise ValueError("Deadline must be at least 1.")
    if using_minute_deadlines():
        return _as_cairo(start_at) + timedelta(minutes=int(deadline_days))
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
        filters={"trainer_item": trainer_item, "node_id": node_id, "status": ["in", ["ACTIVE", "OVERDUE"]]},
        pluck="name",
    ):
        frappe.db.set_value("BEDO Deadline", name, "status", "COMPLETED", update_modified=False)


def _add_deadline_units(value: datetime, quantity: int) -> datetime:
    if int(quantity) < 1:
        raise ValueError("Deadline extension must be at least 1.")
    if using_minute_deadlines():
        return _as_cairo(value) + timedelta(minutes=int(quantity))
    current = _as_cairo(value)
    remaining = int(quantity)
    while remaining:
        current += timedelta(days=1)
        if is_working_day(current):
            remaining -= 1
    return current


def _effective_deadline_units(due_at: datetime) -> int:
    now = datetime.now(CAIRO_TZ)
    effective_seconds = max(0, (_as_cairo(due_at) - now).total_seconds())
    if using_minute_deadlines():
        return int(ceil(effective_seconds / 60)) if effective_seconds else 0
    return max(0, (_as_cairo(due_at).date() - now.date()).days)


def _extend_deadline_doc(doc, extension_units: int) -> dict[str, object]:
    old_due = _as_cairo(doc.due_at)
    new_due = _add_deadline_units(old_due, int(extension_units))
    doc.due_at = to_storage_datetime(new_due)
    doc.deadline_days = int(doc.deadline_days or 0) + int(extension_units)
    doc.status = "ACTIVE"
    doc.overdue_notified_at = None
    doc.reminder_notified_at = None
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    return {
        "name": doc.name,
        "start_at": doc.start_at,
        "due_at": doc.due_at,
        "deadline_days": doc.deadline_days,
        "effective_units": _effective_deadline_units(new_due),
    }


def extend_deadline_by_name(deadline: str, extension_units: int) -> dict[str, object]:
    import frappe

    if not deadline or not frappe.db.exists("BEDO Deadline", deadline):
        raise ValueError("Deadline not found.")
    doc = frappe.get_doc("BEDO Deadline", deadline)
    if doc.status not in {"ACTIVE", "OVERDUE"}:
        raise ValueError("Only active or overdue deadlines can be extended.")
    return _extend_deadline_doc(doc, extension_units)


def extend_active_deadline(trainer_item: str, node_id: str, extension_units: int) -> dict[str, object]:
    import frappe

    name = frappe.db.get_value(
        "BEDO Deadline",
        {"trainer_item": trainer_item, "node_id": node_id, "status": "ACTIVE"},
        "name",
    )
    if not name:
        name = frappe.db.get_value(
            "BEDO Deadline",
            {"trainer_item": trainer_item, "node_id": node_id, "status": "OVERDUE"},
            "name",
        )
    if not name:
        raise ValueError("No active deadline is available for extension.")
    return extend_deadline_by_name(name, extension_units)


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
    import frappe
    from bedo_platform.services.notification_service import notify_many

    now = datetime.now(CAIRO_TZ)
    checked = 0
    sent = 0
    rows = frappe.get_all(
        "BEDO Deadline",
        filters={"status": "ACTIVE", "reminder_notified_at": ["is", "not set"]},
        or_filters=[
            ["start_at", "<=", to_storage_datetime(now)],
            ["due_at", "<=", to_storage_datetime(now + timedelta(hours=2))],
        ],
        fields=["name", "project", "trainer_item", "workflow_type", "node_id", "start_at", "due_at"],
        order_by="due_at asc",
        page_length=500,
    )
    for row in rows:
        checked += 1
        start = _as_cairo(row.start_at)
        due = _as_cairo(row.due_at)
        should_send = now >= start or due - now <= timedelta(hours=2)
        if not should_send:
            continue
        recipients = _deadline_recipients(row.trainer_item, row.node_id)
        if not recipients:
            continue
        notify_many(
            recipients,
            title="SRS deadline active",
            message="An SRS workflow deadline is active or due soon.",
            notification_type="DEADLINE_REMINDER",
            project=row.project,
            trainer_item=row.trainer_item,
            workflow_type=row.workflow_type,
            node_id=row.node_id,
            action_url=project_action_url("srs", row.project, row.trainer_item),
            priority="High",
        )
        frappe.db.set_value("BEDO Deadline", row.name, "reminder_notified_at", to_storage_datetime(now), update_modified=False)
        sent += len(recipients)
    return {"checked": checked, "sent": sent}


def run_overdue_check() -> dict[str, int]:
    import frappe
    from bedo_platform.services.notification_service import notify_many

    now = datetime.now(CAIRO_TZ)
    checked = 0
    sent = 0
    approvals = 0
    rows = frappe.get_all(
        "BEDO Deadline",
        filters={
            "status": "ACTIVE",
            "overdue_notified_at": ["is", "not set"],
            "due_at": ["<=", to_storage_datetime(now)],
        },
        fields=["name", "project", "trainer_item", "workflow_type", "node_id", "due_at"],
        order_by="due_at asc",
        page_length=500,
    )
    for row in rows:
        checked += 1
        if now <= _as_cairo(row.due_at):
            continue
        recipients = _deadline_recipients(row.trainer_item, row.node_id)
        gm_users = _active_users_with_role("General Manager")
        details = _deadline_context(row)
        responsible_message = (
            f"Responsible: {details['responsible_name']} ({details['responsible_user']})."
            if details["responsible_user"]
            else "Responsible: not assigned."
        )
        message = (
            f"{details['project_code']} | {details['project_name']} | {details['trainer_name']} is overdue at "
            f"{details['node_label']}. Due: {details['due_at_label']}. {responsible_message}"
        )
        notify_many(
            recipients,
            title="SRS deadline overdue",
            message=message,
            notification_type="DEADLINE_OVERDUE",
            project=row.project,
            trainer_item=row.trainer_item,
            workflow_type=row.workflow_type,
            node_id=row.node_id,
            action_url=project_action_url("srs", row.project, row.trainer_item),
            priority="High",
        )
        notify_many(
            gm_users,
            title="Deadline extension approval required",
            message=message,
            notification_type="DEADLINE_EXTENSION_APPROVAL_REQUIRED",
            project=row.project,
            trainer_item=row.trainer_item,
            workflow_type=row.workflow_type,
            node_id=row.node_id,
            action_url="/approvals",
            priority="High",
            metadata={"deadline": row.name, "responsible_user": details["responsible_user"]},
        )
        approvals += _create_global_extension_approval(row, details)
        _mark_node_overdue(row.trainer_item, row.node_id, now)
        frappe.db.set_value(
            "BEDO Deadline",
            row.name,
            {"status": "OVERDUE", "overdue_notified_at": to_storage_datetime(now)},
            update_modified=False,
        )
        sent += len(set(recipients + gm_users))
    return {"checked": checked, "sent": sent, "approvals": approvals}


def _active_users_with_role(role: str) -> list[str]:
    import frappe
    from bedo_platform.services.user_profile_service import assert_user_can_login

    users = []
    for row in frappe.get_all("Has Role", filters={"role": role}, fields=["parent"]):
        if row.parent in {"Administrator", "Guest"}:
            continue
        if assert_user_can_login(row.parent):
            users.append(row.parent)
    return sorted(set(users))


def _deadline_context(row) -> dict[str, str]:
    import frappe

    project = frappe.db.get_value("BEDO Project", row.project, ["project_code", "project_name"], as_dict=True) or {}
    trainer = frappe.db.get_value("BEDO Trainer Item", row.trainer_item, ["trainer_item_name"], as_dict=True) or {}
    state = frappe.db.get_value(
        "SRS Workflow Node State",
        {"trainer_item": row.trainer_item, "node_id": row.node_id},
        ["responsible_user"],
        as_dict=True,
    ) or {}
    workflow_owner = frappe.db.get_value("SRS Workflow Instance", {"trainer_item": row.trainer_item}, "project_owner") or ""
    triggered_by = frappe.db.get_value("BEDO Deadline", row.name, "triggered_by") or ""
    responsible = state.get("responsible_user") or workflow_owner or triggered_by
    return {
        "project_code": project.get("project_code") or row.project,
        "project_name": project.get("project_name") or "",
        "trainer_name": trainer.get("trainer_item_name") or row.trainer_item,
        "node_label": _node_label(row.node_id),
        "due_at_label": _format_cairo_datetime(row.due_at),
        "responsible_user": responsible or "",
        "responsible_name": _user_full_name(responsible),
    }


def _format_cairo_datetime(value) -> str:
    return _as_cairo(value).strftime("%b %d, %Y %I:%M %p")


def _node_label(node_id: str) -> str:
    return NODE_LABELS.get(str(node_id or ""), str(node_id or "").replace("_", " ").title())


def _user_full_name(user: str) -> str:
    if not user:
        return ""
    import frappe

    row = frappe.db.get_value("User", user, ["first_name", "last_name", "username"], as_dict=True) or {}
    full_name = " ".join(part for part in [row.get("first_name"), row.get("last_name")] if part)
    return full_name or row.get("username") or user


def _create_global_extension_approval(row, details: dict[str, str]) -> int:
    import frappe

    workflow = frappe.db.get_value("SRS Workflow Instance", {"trainer_item": row.trainer_item}, "name")
    if not workflow:
        return 0
    if frappe.db.exists(
        "SRS Approval",
        {
            "deadline": row.name,
            "approval_type": GLOBAL_DEADLINE_EXTENSION_APPROVAL,
            "status": "WAITING",
        },
    ):
        return 0
    doc = frappe.get_doc(
        {
            "doctype": "SRS Approval",
            "workflow_instance": workflow,
            "project": row.project,
            "trainer_item": row.trainer_item,
            "deadline": row.name,
            "node_id": row.node_id,
            "approval_type": GLOBAL_DEADLINE_EXTENSION_APPROVAL,
            "status": "WAITING",
            "required_role": "General Manager",
            "assigned_to_user": details["responsible_user"],
            "original_deadline_proposal_days": 0,
            "comments": (
                f"Overdue node: {details['node_label']}\n"
                f"Responsible: {details['responsible_name']} ({details['responsible_user'] or 'not assigned'})\n"
                f"Due: {details['due_at_label']}"
            )[:500],
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    return 1


def _mark_node_overdue(trainer_item: str, node_id: str, at: datetime) -> None:
    import frappe

    state = frappe.db.get_value("SRS Workflow Node State", {"trainer_item": trainer_item, "node_id": node_id}, "name")
    if state:
        frappe.db.set_value("SRS Workflow Node State", state, "overdue_at", to_storage_datetime(at), update_modified=False)


def _deadline_recipients(trainer_item: str, node_id: str) -> list[str]:
    import frappe

    users = set()
    state_user = frappe.db.get_value("SRS Workflow Node State", {"trainer_item": trainer_item, "node_id": node_id}, "responsible_user")
    if state_user:
        users.add(state_user)
    owner = frappe.db.get_value("SRS Workflow Instance", {"trainer_item": trainer_item}, "project_owner")
    if owner:
        users.add(owner)
    team_users = frappe.get_all("SRS Item Team Member", filters={"trainer_item": trainer_item}, pluck="user")
    users.update(team_users)
    return sorted(user for user in users if user)
