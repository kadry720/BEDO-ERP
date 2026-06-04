from __future__ import annotations

from typing import Any

from bedo_platform.services.auth_service import USERNAME_RE
from bedo_platform.services.security_audit_service import log_security_event


def get_current_profile() -> dict[str, Any]:
    import frappe

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("You must be logged in to view your profile.", frappe.PermissionError)

    doc = frappe.get_doc("User", user)
    return {
        "user": doc.name,
        "username": doc.username or "",
        "first_name": doc.first_name or "",
        "middle_name": doc.middle_name or "",
        "last_name": doc.last_name or "",
    }


def update_current_profile(payload: dict[str, Any]) -> dict[str, Any]:
    import frappe

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("You must be logged in to update your profile.", frappe.PermissionError)

    username = str(payload.get("username", "")).strip()
    first_name = str(payload.get("first_name", "")).strip()
    middle_name = str(payload.get("middle_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()
    password = str(payload.get("password", "")).strip()

    if not USERNAME_RE.match(username):
        raise ValueError("Username may contain only letters, numbers, dot, dash, and underscore.")
    if not first_name:
        raise ValueError("First name is required.")
    if len(first_name) > 140 or len(middle_name) > 140 or len(last_name) > 140:
        raise ValueError("Names must be 140 characters or less.")

    doc = frappe.get_doc("User", user)
    doc.username = username
    doc.first_name = first_name
    doc.middle_name = middle_name
    doc.last_name = last_name
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)

    if password:
        from frappe.core.doctype.user.user import _update_password

        _update_password(user, password, logout_all_sessions=0)

    log_security_event("profile_update", user=user, status="Success")
    return {"success": True, "profile": get_current_profile()}
