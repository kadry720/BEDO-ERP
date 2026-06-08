from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.parse import quote, unquote


NOTIFICATION_TYPE_LABELS = {
    "PROJECT_RELEASED_TO_SRS": "New trainer released to SRS",
    "PROJECT_OWNER_ASSIGNED": "Project owner assigned",
    "DEADLINE_STARTING": "Deadline starting",
    "DEADLINE_REMINDER": "Deadline due soon",
    "DEADLINE_OVERDUE": "Deadline overdue",
    "APPROVAL_REQUIRED": "Approval required",
    "GM_APPROVAL_REQUIRED": "Approval required",
    "SRS_MANAGER_APPROVAL_REQUIRED": "Approval required",
    "GM_APPROVAL_COMPLETED": "Approval completed",
    "SRS_MANAGER_APPROVAL_COMPLETED": "Approval completed",
    "BMDP_SUBMITTED": "BMDP submitted",
    "SRS_WORKFLOW_COMPLETED": "SRS complete",
    "DEADLINE_LOCKED": "Deadline starting",
}


def _notification_label(notification_type: str) -> str:
    return NOTIFICATION_TYPE_LABELS.get(notification_type, notification_type.replace("_", " ").title())


def route_id(value: str) -> str:
    return quote(unquote(str(value or "")), safe="")


def project_action_url(scope: str, project: str, trainer_item: str = "", suffix: str = "") -> str:
    base = f"/{scope}/projects/{route_id(project)}"
    if trainer_item:
        return f"{base}/items/{route_id(trainer_item)}"
    return f"{base}{suffix}"


def normalize_project_action_url(action_url: str, project: str = "", trainer_item: str = "") -> str:
    if not action_url.startswith("/"):
        return action_url
    for scope in ("gm", "srs"):
        prefix = f"/{scope}/projects/"
        if not action_url.startswith(prefix):
            continue
        tail = action_url[len(prefix):]
        if "/items/" in tail:
            raw_project, raw_item = tail.split("/items/", 1)
            return project_action_url(scope, project or raw_project, trainer_item or raw_item)
        if tail.endswith("/trainers"):
            raw_project = tail[: -len("/trainers")]
            return project_action_url(scope, project or raw_project, suffix="/trainers")
        return project_action_url(scope, project or tail)
    return action_url


def create_notification(
    *,
    recipient_user: str,
    title: str,
    message: str,
    notification_type: str,
    project: str = "",
    trainer_item: str = "",
    workflow_type: str = "SRS",
    node_id: str = "",
    action_url: str = "",
    priority: str = "Normal",
    metadata: dict[str, Any] | None = None,
) -> str:
    import frappe

    doc = frappe.get_doc(
        {
            "doctype": "BEDO Notification",
            "recipient_user": recipient_user,
            "project": project,
            "trainer_item": trainer_item,
            "workflow_type": workflow_type,
            "node_id": node_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "action_url": action_url,
            "priority": priority,
            "is_read": 0,
            "created_at": datetime.utcnow(),
            "metadata_safe_json": json.dumps(metadata or {}, sort_keys=True),
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    return doc.name


def notify_many(recipients: list[str], **kwargs: Any) -> None:
    for recipient in sorted(set(filter(None, recipients))):
        create_notification(recipient_user=recipient, **kwargs)


def list_my_notifications(user: str, limit: int = 25) -> dict[str, Any]:
    import frappe

    rows = frappe.get_all(
        "BEDO Notification",
        filters={"recipient_user": user},
        fields=["name", "notification_type", "title", "message", "action_url", "priority", "is_read", "created_at", "project", "trainer_item", "node_id"],
        order_by="created_at desc",
        page_length=min(max(int(limit or 25), 1), 100),
    )
    unread = frappe.db.count("BEDO Notification", {"recipient_user": user, "is_read": 0})
    safe_rows = []
    for row in rows:
        project = frappe.db.get_value("BEDO Project", row.project, ["project_code", "project_name"], as_dict=True) if row.project else {}
        trainer = frappe.db.get_value("BEDO Trainer Item", row.trainer_item, ["trainer_item_name"], as_dict=True) if row.trainer_item else {}
        safe_rows.append(
            {
                **dict(row),
                "type_label": _notification_label(row.notification_type),
                "action_url": normalize_project_action_url(row.action_url or "", row.project or "", row.trainer_item or ""),
                "project_code": (project or {}).get("project_code") or "",
                "project_name": (project or {}).get("project_name") or "",
                "trainer_item_name": (trainer or {}).get("trainer_item_name") or "",
            }
        )
    return {"notifications": safe_rows, "unread": unread}


def mark_notification_read(user: str, notification: str) -> dict[str, bool]:
    import frappe

    owner = frappe.db.get_value("BEDO Notification", notification, "recipient_user")
    if owner != user:
        frappe.throw("Notification not found.", frappe.PermissionError)
    frappe.db.set_value("BEDO Notification", notification, {"is_read": 1, "read_at": datetime.utcnow()})
    return {"success": True}


def mark_all_notifications_read(user: str) -> dict[str, bool]:
    import frappe

    for name in frappe.get_all("BEDO Notification", filters={"recipient_user": user, "is_read": 0}, pluck="name"):
        frappe.db.set_value("BEDO Notification", name, {"is_read": 1, "read_at": datetime.utcnow()})
    return {"success": True}
