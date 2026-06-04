from __future__ import annotations

from bedo_platform.constants import FRAPPE_DESK_TECHNICAL_ROLES
from bedo_platform.services.security_audit_service import log_security_event


DESK_PATH_PREFIXES = ("/app", "/desk")


def is_technical_desk_user(user: str) -> bool:
    if user == "Administrator":
        return True
    if not user or user == "Guest":
        return False
    try:
        import frappe

        roles = set(frappe.get_roles(user))
        return bool(roles & FRAPPE_DESK_TECHNICAL_ROLES)
    except Exception:
        return False


def restrict_frappe_desk() -> None:
    import frappe

    request = getattr(frappe.local, "request", None)
    if not request:
        return

    path = request.path or ""
    if path.startswith("/api/") or path.startswith("/assets/") or path.startswith("/files/"):
        return
    if not path.startswith(DESK_PATH_PREFIXES):
        return

    user = getattr(frappe.session, "user", "Guest")
    if is_technical_desk_user(user):
        return

    log_security_event(
        "frappe_desk_access_blocked",
        user=user if user != "Guest" else None,
        status="Failure",
        message=f"Blocked Desk path: {path}",
    )
    frappe.throw("Frappe Desk is restricted to BEDO technical administrators.", frappe.PermissionError)
