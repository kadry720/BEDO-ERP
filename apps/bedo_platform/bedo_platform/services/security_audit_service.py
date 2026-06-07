from __future__ import annotations

from datetime import datetime
from typing import Any

from bedo_platform.constants import SECURITY_AUDIT_ROLES

SENSITIVE_TOKENS = ("password", "bind", "secret", "token")


def sanitize_message(message: str | None) -> str:
    if not message:
        return ""
    safe = str(message)
    lowered = safe.lower()
    if any(token in lowered for token in SENSITIVE_TOKENS):
        return "[redacted security message]"
    return safe[:500]


def log_security_event(
    event_type: str,
    *,
    username: str | None = None,
    user: str | None = None,
    target_user: str | None = None,
    project: str | None = None,
    trainer_item: str | None = None,
    workflow_type: str | None = None,
    node_id: str | None = None,
    status: str = "Success",
    message: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    try:
        import frappe
    except Exception:
        return

    ip_address = ""
    user_agent = ""
    if getattr(frappe, "local", None) and getattr(frappe.local, "request", None):
        ip_address = frappe.local.request_ip or ""
        user_agent = frappe.local.request.headers.get("User-Agent", "")

    target_username = ""
    if target_user:
        target_username = frappe.db.get_value("User", target_user, "username") or ""

    doc = frappe.get_doc(
        {
            "doctype": "BEDO Security Event",
            "event_type": event_type,
            "username": username or "",
            "user": user or "",
            "target_user": target_user or "",
            "target_username": target_username,
            "project": project or "",
            "trainer_item": trainer_item or "",
            "workflow_type": workflow_type or "",
            "node_id": node_id or "",
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent[:250],
            "message": sanitize_message(message),
            "created_at": datetime.utcnow(),
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)


def list_security_events_for_user(user: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    import frappe

    roles = set(frappe.get_roles(user))
    if not roles & SECURITY_AUDIT_ROLES:
        frappe.throw("You do not have access to BEDO security logs.", frappe.PermissionError)

    filters = filters or {}
    page = max(int(filters.get("page") or 1), 1)
    page_size = min(max(int(filters.get("page_size") or filters.get("limit") or 50), 1), 200)
    start = (page - 1) * page_size

    query_filters: list[Any] = []
    date_from = str(filters.get("date_from") or "").strip()
    date_to = str(filters.get("date_to") or "").strip()
    event_type = str(filters.get("event_type") or "").strip()
    actor = str(filters.get("actor") or "").strip()
    target_user = str(filters.get("target_user") or "").strip()
    project = str(filters.get("project") or "").strip()
    trainer_item = str(filters.get("trainer_item") or "").strip()
    status = str(filters.get("status") or "").strip()
    search = str(filters.get("search") or filters.get("query") or "").strip()

    if date_from:
        if len(date_from) == 10:
            date_from = f"{date_from} 00:00:00"
        query_filters.append(["created_at", ">=", date_from])
    if date_to:
        if len(date_to) == 10:
            date_to = f"{date_to} 23:59:59"
        query_filters.append(["created_at", "<=", date_to])
    if event_type:
        query_filters.append(["event_type", "=", event_type])
    if actor:
        query_filters.append(["user", "like", f"%{actor}%"])
    if target_user:
        query_filters.append(["target_user", "like", f"%{target_user}%"])
    if project:
        query_filters.append(["project", "=", project])
    if trainer_item:
        query_filters.append(["trainer_item", "=", trainer_item])
    if status in {"Success", "Failure"}:
        query_filters.append(["status", "=", status])

    or_filters = []
    if search:
        like = f"%{search}%"
        or_filters = [
            ["username", "like", like],
            ["user", "like", like],
            ["target_user", "like", like],
            ["target_username", "like", like],
            ["event_type", "like", like],
            ["project", "like", like],
            ["trainer_item", "like", like],
        ]

    fields = [
        "event_type",
        "username",
        "user",
        "target_user",
        "target_username",
        "project",
        "trainer_item",
        "workflow_type",
        "node_id",
        "status",
        "ip_address",
        "user_agent",
        "message",
        "created_at",
    ]
    total = frappe.db.count("BEDO Security Event", filters=query_filters)
    rows = frappe.get_all(
        "BEDO Security Event",
        fields=fields,
        filters=query_filters,
        or_filters=or_filters,
        order_by="created_at desc",
        start=start,
        page_length=page_size,
    )
    return {"events": rows, "page": page, "page_size": page_size, "total": total}
