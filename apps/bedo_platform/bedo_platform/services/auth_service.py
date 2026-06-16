from __future__ import annotations

import re
from typing import Any

from bedo_platform.constants import ALL_ROLE_NAMES
from bedo_platform.services.database_auth_service import authenticate_user
from bedo_platform.services.routing_service import get_current_user_landing_route, get_visible_dashboards_for_user
from bedo_platform.services.security_audit_service import log_security_event
from bedo_platform.services.user_profile_service import assert_user_can_login

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{2,64}$")


def validate_username(username: str) -> str:
    username = (username or "").strip()
    if not USERNAME_RE.match(username):
        raise ValueError("Invalid username.")
    return username


def _request_ip() -> str:
    try:
        import frappe

        request = getattr(frappe.local, "request", None)
        forwarded = request.headers.get("X-Forwarded-For", "") if request else ""
        return (forwarded.split(",")[0].strip() or getattr(frappe.local, "request_ip", "") or "")[:64]
    except Exception:
        return ""


def _rate_limit_keys(username: str, ip_address: str = "") -> list[str]:
    keys = [f"bedo_login_failures:{username}"]
    if ip_address:
        keys.append(f"bedo_login_failures:{username}:{ip_address}")
    return keys


def is_rate_limited(username: str, ip_address: str = "") -> bool:
    try:
        import frappe

        cache = frappe.cache()
        return any(int(cache.get_value(key) or 0) >= 5 for key in _rate_limit_keys(username, ip_address))
    except Exception:
        return False


def record_failed_attempt(username: str, ip_address: str = "") -> None:
    try:
        import frappe

        cache = frappe.cache()
        for key in _rate_limit_keys(username, ip_address):
            failures = int(cache.get_value(key) or 0) + 1
            cache.set_value(key, failures, expires_in_sec=900)
    except Exception:
        return


def clear_failed_attempts(username: str, ip_address: str = "") -> None:
    try:
        import frappe

        cache = frappe.cache()
        for key in _rate_limit_keys(username, ip_address):
            cache.delete_value(key)
    except Exception:
        return


def get_safe_user_context(user: str) -> dict[str, Any]:
    import frappe

    if not assert_user_can_login(user):
        frappe.throw("This BEDO account is inactive.", frappe.PermissionError)

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
    ip_address = _request_ip()
    if username.lower() in {"administrator", "admin"}:
        log_security_event(
            "login_failure",
            username="Administrator",
            status="Failure",
            message="Administrator web login is not allowed",
        )
        return {"success": False, "message": "Invalid username or password."}
    if not password:
        record_failed_attempt(username, ip_address)
        log_security_event("login_failure", username=username, status="Failure", message="Missing password")
        return {"success": False, "message": "Invalid username or password."}
    if is_rate_limited(username, ip_address):
        log_security_event("login_failure", username=username, status="Failure", message="Rate limit exceeded")
        return {"success": False, "message": "Invalid username or password."}

    db_user = authenticate_user(username, password)
    if not db_user:
        record_failed_attempt(username, ip_address)
        log_security_event("login_failure", username=username, status="Failure", message="Invalid credentials")
        return {"success": False, "message": "Invalid username or password."}

    if not assert_user_can_login(db_user.user):
        record_failed_attempt(username, ip_address)
        log_security_event("login_failure", username=username, user=db_user.user, status="Failure", message="Inactive BEDO account")
        return {"success": False, "message": "Invalid username or password."}

    clear_failed_attempts(username, ip_address)
    log_security_event("login_success", username=username, user=db_user.user, status="Success")
    return {"success": True, "context": get_safe_user_context(db_user.user)}


def login(username: str, password: str) -> dict[str, Any]:
    import frappe

    username = validate_username(username)
    ip_address = _request_ip()
    if not password:
        record_failed_attempt(username, ip_address)
        log_security_event("login_failure", username=username, status="Failure", message="Missing password")
        return {"success": False, "message": "Invalid username or password."}

    if is_rate_limited(username, ip_address):
        log_security_event("login_failure", username=username, status="Failure", message="Rate limit exceeded")
        return {"success": False, "message": "Too many login attempts. Try again later."}

    if username.lower() in {"administrator", "admin"}:
        try:
            frappe.local.login_manager.authenticate(user="Administrator", pwd=password)
            frappe.local.login_manager.post_login()
            clear_failed_attempts(username, ip_address)
            log_security_event("login_success", username="Administrator", user="Administrator", status="Success")
            return {"success": True, "route": "/app"}
        except Exception:
            record_failed_attempt(username, ip_address)
            log_security_event(
                "login_failure",
                username="Administrator",
                status="Failure",
                message="Invalid administrator credentials",
            )
            return {"success": False, "message": "Invalid username or password."}

    db_user = authenticate_user(username, password)
    if not db_user:
        record_failed_attempt(username, ip_address)
        log_security_event("login_failure", username=username, status="Failure", message="Invalid credentials")
        return {"success": False, "message": "Invalid username or password."}

    if not assert_user_can_login(db_user.user):
        record_failed_attempt(username, ip_address)
        log_security_event("login_failure", username=username, user=db_user.user, status="Failure", message="Inactive BEDO account")
        return {"success": False, "message": "Invalid username or password."}

    clear_failed_attempts(username, ip_address)
    frappe.local.login_manager.login_as(db_user.user)
    route = get_current_user_landing_route(db_user.user)
    log_security_event("login_success", username=username, user=db_user.user, status="Success")
    return {"success": True, "route": route}


def database_request_auth_hook() -> None:
    return None


def enforce_database_session(login_manager: object | None = None) -> None:
    return None


def record_logout(login_manager: object | None = None) -> None:
    try:
        import frappe

        user = getattr(frappe.session, "user", None)
        if user and user != "Guest":
            log_security_event("logout", user=user, status="Success")
    except Exception:
        return
