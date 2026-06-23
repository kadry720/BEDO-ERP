from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, unquote
from zoneinfo import ZoneInfo

CAIRO_TZ = ZoneInfo("Africa/Cairo")


NOTIFICATION_TYPE_LABELS = {
    "PROJECT_RELEASED_TO_SRS": "New trainer released to SRS",
    "PROJECT_OWNER_ASSIGNED": "Project owner assigned",
    "SRS_TEAM_ASSIGNED": "SRS team assignment",
    "DEADLINE_STARTING": "Deadline starting",
    "DEADLINE_REMINDER": "Deadline due soon",
    "DEADLINE_OVERDUE": "Deadline overdue",
    "DEADLINE_EXTENSION_APPROVAL_REQUIRED": "Deadline extension approval required",
    "DEADLINE_EXTENSION_APPROVED": "Deadline extension approved",
    "APPROVAL_REQUIRED": "Approval required",
    "GM_APPROVAL_REQUIRED": "Approval required",
    "SRS_MANAGER_APPROVAL_REQUIRED": "Approval required",
    "GM_APPROVAL_COMPLETED": "Approval completed",
    "SRS_MANAGER_APPROVAL_COMPLETED": "Approval completed",
    "BMDP_SUBMITTED": "BMDP submitted",
    "SRS_WORKFLOW_COMPLETED": "SRS complete",
    "DEADLINE_LOCKED": "Deadline starting",
}


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _utc_to_cairo_iso(value: datetime | str | None) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(CAIRO_TZ).isoformat()


def _notification_label(notification_type: str) -> str:
    return NOTIFICATION_TYPE_LABELS.get(notification_type, notification_type.replace("_", " ").title())


def route_id(value: str) -> str:
    return quote(unquote(str(value or "")), safe="")


def route_path_id(value: str) -> str:
    return "/".join(route_id(part) for part in unquote(str(value or "")).split("/") if part)


def project_action_url(scope: str, project: str, trainer_item: str = "", suffix: str = "") -> str:
    base = f"/{scope}/project/{route_path_id(project)}"
    if trainer_item:
        return f"{base}/items/{route_id(trainer_item)}"
    return f"{base}{suffix}"


def normalize_project_action_url(action_url: str, project: str = "", trainer_item: str = "") -> str:
    if not action_url.startswith("/"):
        return action_url
    for scope in ("gm", "srs", "command-center"):
        for prefix in (f"/{scope}/project/", f"/{scope}/projects/"):
            if not action_url.startswith(prefix):
                continue
            tail = action_url[len(prefix):]
            if "/items/" in tail:
                raw_project, raw_item = tail.rsplit("/items/", 1)
                return project_action_url(scope, project or raw_project, trainer_item or raw_item)
            if tail.endswith("/trainers"):
                raw_project = tail[: -len("/trainers")]
                return project_action_url(scope, project or raw_project, suffix="/trainers")
            return project_action_url(scope, project or tail)
    return action_url


def _project_action_url_parts(action_url: str) -> tuple[str, str]:
    suffix = ""
    if action_url.endswith("/trainers"):
        suffix = "/trainers"
    if action_url.startswith(("/command-center/project/", "/command-center/projects/")):
        return "command-center", suffix
    preferred_scope = "srs" if action_url.startswith(("/srs/project/", "/srs/projects/")) else "gm"
    return preferred_scope, suffix


def project_action_url_for_user(
    user: str,
    action_url: str,
    project: str = "",
    trainer_item: str = "",
) -> str:
    normalized_url = normalize_project_action_url(action_url or "", project, trainer_item)
    if not project or not normalized_url.startswith(("/gm/project/", "/srs/project/", "/command-center/project/", "/gm/projects/", "/srs/projects/", "/command-center/projects/")):
        return normalized_url

    import frappe

    from bedo_platform.services.routing_service import resolve_landing_route, route_allowed_for_roles

    preferred_scope, suffix = _project_action_url_parts(normalized_url)
    roles = frappe.get_roles(user)
    scopes = [preferred_scope] + [scope for scope in ("gm", "srs", "command-center") if scope != preferred_scope]
    for scope in scopes:
        if route_allowed_for_roles(f"/{scope}", roles):
            return project_action_url(scope, project, trainer_item, suffix)
    return resolve_landing_route(roles)


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

    metadata_payload = metadata or {}
    metadata_json = json.dumps(metadata_payload, sort_keys=True)
    if metadata_payload.get("event_key"):
        existing = frappe.db.get_value(
            "BEDO Notification",
            {
                "recipient_user": recipient_user,
                "notification_type": notification_type,
                "project": project,
                "trainer_item": trainer_item,
                "node_id": node_id,
                "metadata_safe_json": metadata_json,
                "is_read": 0,
            },
            "name",
        )
        if existing:
            return existing

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
            "action_url": project_action_url_for_user(recipient_user, action_url, project, trainer_item),
            "priority": priority,
            "is_read": 0,
            "created_at": _utcnow(),
            "metadata_safe_json": metadata_json,
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
        safe_row = dict(row)
        safe_row["created_at"] = _utc_to_cairo_iso(row.created_at)
        safe_rows.append(
            {
                **safe_row,
                "type_label": _notification_label(row.notification_type),
                "action_url": project_action_url_for_user(user, row.action_url or "", row.project or "", row.trainer_item or ""),
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
    frappe.db.set_value("BEDO Notification", notification, {"is_read": 1, "read_at": _utcnow()})
    return {"success": True}


def mark_notification_unread(user: str, notification: str) -> dict[str, bool]:
    import frappe

    owner = frappe.db.get_value("BEDO Notification", notification, "recipient_user")
    if owner != user:
        frappe.throw("Notification not found.", frappe.PermissionError)
    frappe.db.set_value("BEDO Notification", notification, {"is_read": 0, "read_at": None})
    return {"success": True}


def mark_all_notifications_read(user: str) -> dict[str, bool]:
    import frappe

    for name in frappe.get_all("BEDO Notification", filters={"recipient_user": user, "is_read": 0}, pluck="name"):
        frappe.db.set_value("BEDO Notification", name, {"is_read": 1, "read_at": _utcnow()})
    return {"success": True}
