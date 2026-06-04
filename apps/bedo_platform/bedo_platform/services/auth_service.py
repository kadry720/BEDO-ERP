from __future__ import annotations

import re
from typing import Any

from bedo_platform.constants import ALL_ROLE_NAMES
from bedo_platform.services import ldap_service
from bedo_platform.services.routing_service import get_current_user_landing_route, get_visible_dashboards_for_user
from bedo_platform.services.security_audit_service import log_security_event

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{2,64}$")


def validate_username(username: str) -> str:
    username = (username or "").strip()
    if not USERNAME_RE.match(username):
        raise ValueError("Invalid username.")
    return username


def is_rate_limited(username: str) -> bool:
    try:
        import frappe

        cache = frappe.cache()
        key = f"bedo_login_failures:{username}"
        failures = int(cache.get_value(key) or 0)
        return failures >= 5
    except Exception:
        return False


def record_failed_attempt(username: str) -> None:
    try:
        import frappe

        cache = frappe.cache()
        key = f"bedo_login_failures:{username}"
        failures = int(cache.get_value(key) or 0) + 1
        cache.set_value(key, failures, expires_in_sec=900)
    except Exception:
        return


def clear_failed_attempts(username: str) -> None:
    try:
        import frappe

        frappe.cache().delete_value(f"bedo_login_failures:{username}")
    except Exception:
        return


def sync_frappe_user(ldap_user: ldap_service.LDAPUser) -> str:
    import frappe

    email = ldap_user.email or f"{ldap_user.username}@bedo.local"
    existing = frappe.db.get_value("User", {"username": ldap_user.username}, "name")
    existing = existing or frappe.db.get_value("User", {"email": email}, "name")
    if existing:
        user_doc = frappe.get_doc("User", existing)
        user_doc.username = ldap_user.username
        user_doc.first_name = ldap_user.first_name or user_doc.first_name or ldap_user.username
        user_doc.last_name = ldap_user.last_name or user_doc.last_name
        user_doc.phone = ldap_user.phone_number or user_doc.phone
        user_doc.enabled = 1
        user_doc.flags.ignore_permissions = True
        user_doc.save(ignore_permissions=True)
        return user_doc.name

    user_doc = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "username": ldap_user.username,
            "first_name": ldap_user.first_name or ldap_user.username,
            "last_name": ldap_user.last_name or "",
            "phone": ldap_user.phone_number or "",
            "enabled": 1,
            "send_welcome_email": 0,
        }
    )
    user_doc.flags.ignore_permissions = True
    user_doc.flags.no_reset_password = True
    user_doc.insert(ignore_permissions=True)
    return user_doc.name


def get_safe_user_context(user: str) -> dict[str, Any]:
    import frappe

    user_doc = frappe.get_doc("User", user)
    roles = [role for role in frappe.get_roles(user) if role in ALL_ROLE_NAMES]
    return {
        "user": user_doc.name,
        "username": user_doc.username or user_doc.name,
        "first_name": user_doc.first_name or "",
        "middle_name": getattr(user_doc, "middle_name", "") or "",
        "last_name": user_doc.last_name or "",
        "email": user_doc.email or "",
        "phone_number": user_doc.phone or "",
        "enabled": int(user_doc.enabled or 0),
        "roles": roles,
        "landing_route": get_current_user_landing_route(user),
        "modules": get_visible_dashboards_for_user(user),
    }


def login_for_web(username: str, password: str) -> dict[str, Any]:
    username = validate_username(username)
    if username.lower() in {"administrator", "admin"}:
        log_security_event(
            "login_failure",
            username="Administrator",
            status="Failure",
            message="Administrator web login is not allowed",
        )
        return {"success": False, "message": "Invalid username or password."}
    if not password:
        record_failed_attempt(username)
        log_security_event("login_failure", username=username, status="Failure", message="Missing password")
        return {"success": False, "message": "Invalid username or password."}
    if is_rate_limited(username):
        log_security_event("login_failure", username=username, status="Failure", message="Rate limit exceeded")
        return {"success": False, "message": "Invalid username or password."}

    try:
        ldap_user = ldap_service.authenticate(username, password)
    except Exception:
        record_failed_attempt(username)
        log_security_event("login_failure", username=username, status="Failure", message="LDAP authentication failed")
        return {"success": False, "message": "Invalid username or password."}

    if not ldap_user:
        record_failed_attempt(username)
        log_security_event("login_failure", username=username, status="Failure", message="Invalid credentials")
        return {"success": False, "message": "Invalid username or password."}

    user = sync_frappe_user(ldap_user)
    clear_failed_attempts(username)
    log_security_event("login_success", username=username, user=user, status="Success")
    return {"success": True, "context": get_safe_user_context(user)}


def login(username: str, password: str) -> dict[str, Any]:
    import frappe

    username = validate_username(username)
    if not password:
        record_failed_attempt(username)
        log_security_event("login_failure", username=username, status="Failure", message="Missing password")
        return {"success": False, "message": "Invalid username or password."}

    if is_rate_limited(username):
        log_security_event("login_failure", username=username, status="Failure", message="Rate limit exceeded")
        return {"success": False, "message": "Too many login attempts. Try again later."}

    if username.lower() in {"administrator", "admin"}:
        try:
            frappe.local.login_manager.authenticate(user="Administrator", pwd=password)
            frappe.local.login_manager.post_login()
            clear_failed_attempts(username)
            log_security_event("login_success", username="Administrator", user="Administrator", status="Success")
            return {"success": True, "route": "/app"}
        except Exception:
            record_failed_attempt(username)
            log_security_event(
                "login_failure",
                username="Administrator",
                status="Failure",
                message="Invalid administrator credentials",
            )
            return {"success": False, "message": "Invalid username or password."}

    try:
        ldap_user = ldap_service.authenticate(username, password)
    except Exception:
        record_failed_attempt(username)
        log_security_event("login_failure", username=username, status="Failure", message="LDAP authentication failed")
        return {"success": False, "message": "Invalid username or password."}

    if not ldap_user:
        record_failed_attempt(username)
        log_security_event("login_failure", username=username, status="Failure", message="Invalid credentials")
        return {"success": False, "message": "Invalid username or password."}

    user = sync_frappe_user(ldap_user)
    clear_failed_attempts(username)
    frappe.flags.bedo_ldap_login = True
    frappe.local.login_manager.login_as(user)
    route = get_current_user_landing_route(user)
    log_security_event("login_success", username=username, user=user, status="Success")
    return {"success": True, "route": route}


def ldap_request_auth_hook() -> None:
    return None


def enforce_ldap_only_session(login_manager: object | None = None) -> None:
    try:
        import frappe

        user = getattr(frappe.session, "user", "")
        if not user or user in {"Guest", "Administrator"}:
            return
        if getattr(frappe.flags, "bedo_ldap_login", False):
            return
        roles = set(frappe.get_roles(user))
        if roles & set(ALL_ROLE_NAMES):
            log_security_event(
                "login_failure",
                user=user,
                status="Failure",
                message="Blocked local password fallback for BEDO business user",
            )
            frappe.local.login_manager.logout()
            frappe.throw("BEDO business users must sign in through LDAP.", frappe.AuthenticationError)
    except Exception:
        raise


def record_logout(login_manager: object | None = None) -> None:
    try:
        import frappe

        user = getattr(frappe.session, "user", None)
        if user and user != "Guest":
            log_security_event("logout", user=user, status="Success")
    except Exception:
        return
