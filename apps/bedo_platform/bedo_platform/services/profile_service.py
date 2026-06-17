from __future__ import annotations

from typing import Any

from bedo_platform.services.auth_service import USERNAME_RE
from bedo_platform.services.database_auth_service import check_current_password, enforce_password_policy, set_user_password
from bedo_platform.services.security_audit_service import log_security_event
from bedo_platform.services.user_profile_service import assert_user_can_login, ensure_user_profile
from bedo_platform.services.user_management_service import EMAIL_RE, PHONE_RE


def _resolve_profile_user(user: str | None = None) -> str:
    import frappe

    user = user or frappe.session.user
    if not user or user == "Guest":
        frappe.throw("You must be logged in to view your profile.", frappe.PermissionError)
    if not assert_user_can_login(user):
        frappe.throw("This BEDO account is inactive.", frappe.PermissionError)
    return user


def get_current_profile(user: str | None = None) -> dict[str, Any]:
    import frappe

    user = _resolve_profile_user(user)
    doc = frappe.get_doc("User", user)
    return {
        "user": doc.name,
        "username": doc.username or "",
        "first_name": doc.first_name or "",
        "middle_name": doc.middle_name or "",
        "last_name": doc.last_name or "",
        "email": doc.email or "",
        "phone_number": doc.phone or "",
    }


def _identity_payload(payload: dict[str, Any]) -> dict[str, str]:
    username = str(payload.get("username", "")).strip()
    first_name = str(payload.get("first_name", "")).strip()
    middle_name = str(payload.get("middle_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()
    email = str(payload.get("email", "")).strip()
    phone_number = str(payload.get("phone_number", "")).strip()

    if not USERNAME_RE.match(username):
        raise ValueError("Username may contain only letters, numbers, dot, dash, and underscore.")
    if not first_name:
        raise ValueError("First name is required.")
    if not last_name:
        raise ValueError("Last name is required.")
    if not EMAIL_RE.match(email):
        raise ValueError("A valid email address is required.")
    if not PHONE_RE.match(phone_number):
        raise ValueError("A valid phone number is required.")
    if len(first_name) > 140 or len(middle_name) > 140 or len(last_name) > 140:
        raise ValueError("Names must be 140 characters or less.")
    return {
        "username": username,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone_number,
    }


def _password_payload(payload: dict[str, Any]) -> tuple[str, str, str] | None:
    current_password = str(payload.get("current_password", "") or "")
    new_password = str(payload.get("new_password", "") or payload.get("password", "") or "")
    confirm_password = str(payload.get("confirm_password", "") or "")
    if not current_password and not new_password and not confirm_password:
        return None
    if not new_password:
        raise ValueError("New password is required.")
    if not current_password:
        raise ValueError("Current password is required to change your password.")
    if new_password != confirm_password:
        raise ValueError("New password and confirmation must match.")
    return current_password, new_password, confirm_password


def update_current_profile(payload: dict[str, Any], user: str | None = None) -> dict[str, Any]:
    import frappe

    user = _resolve_profile_user(user)
    identity = _identity_payload(payload)
    password_change = _password_payload(payload)

    doc = frappe.get_doc("User", user)
    doc.username = identity["username"]
    doc.first_name = identity["first_name"]
    doc.middle_name = identity["middle_name"]
    doc.last_name = identity["last_name"]
    doc.email = identity["email"]
    doc.phone = identity["phone_number"]
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    ensure_user_profile(user, identity["username"], active=True, deleted=False)

    password_changed = False
    if password_change:
        current_password, new_password, _confirm_password = password_change
        if not check_current_password(user, current_password):
            raise ValueError("Current password is incorrect.")
        enforce_password_policy(
            new_password,
            username=identity["username"],
            email=identity["email"],
            first_name=identity["first_name"],
            last_name=identity["last_name"],
        )
        set_user_password(user, new_password, logout_all_sessions=False)
        password_changed = True
        log_security_event("password_change", user=user, status="Success")

    log_security_event("profile_update", user=user, status="Success")
    from bedo_platform.services.auth_service import get_safe_user_context

    return {
        "success": True,
        "profile": get_current_profile(user),
        "context": get_safe_user_context(user),
        "password_changed": password_changed,
    }
