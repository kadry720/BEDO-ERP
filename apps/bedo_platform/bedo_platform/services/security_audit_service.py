from __future__ import annotations

from datetime import datetime
from typing import Any

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

    doc = frappe.get_doc(
        {
            "doctype": "BEDO Security Event",
            "event_type": event_type,
            "username": username or "",
            "user": user or "",
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent[:250],
            "message": sanitize_message(message),
            "created_at": datetime.utcnow(),
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
