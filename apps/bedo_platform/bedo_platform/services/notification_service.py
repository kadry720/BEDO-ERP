from __future__ import annotations

import json
from datetime import datetime
from typing import Any


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
    return {"notifications": rows, "unread": unread}


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
