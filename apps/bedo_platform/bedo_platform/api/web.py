from __future__ import annotations

import frappe

from bedo_platform.constants import ALL_ROLE_NAMES, DEPARTMENTS, FRAPPE_DESK_TECHNICAL_ROLES
from bedo_platform.services.auth_service import get_safe_user_context, login_for_web
from bedo_platform.services.profile_service import get_current_profile, update_current_profile
from bedo_platform.services.routing_service import ensure_dashboard_access, get_current_user_landing_route
from bedo_platform.services.service_auth import require_service_auth, validate_service_request
from bedo_platform.services.user_management_service import (
    create_user_from_admin,
    disable_user,
    list_users_for_admin,
    update_user_roles,
)


def _payload(value):
    if isinstance(value, str):
        return frappe.parse_json(value)
    return value or {}


@frappe.whitelist(allow_guest=True)
@require_service_auth
def login(username: str, password: str):
    return login_for_web(username, password)


@frappe.whitelist(allow_guest=True)
def me():
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return get_safe_user_context(user)


@frappe.whitelist(allow_guest=True)
def logout():
    user = validate_service_request()
    if user:
        from bedo_platform.services.security_audit_service import log_security_event

        log_security_event("logout", user=user, status="Success")
    return {"success": True}


@frappe.whitelist(allow_guest=True)
def get_landing_route():
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return {"route": get_current_user_landing_route(user)}


@frappe.whitelist(allow_guest=True)
def ensure_route_access(route: str):
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return ensure_dashboard_access(route, user)


@frappe.whitelist(allow_guest=True)
def get_admin_bootstrap():
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return {
        "roles": ALL_ROLE_NAMES,
        "departments": DEPARTMENTS,
        "technical_desk_roles": sorted(FRAPPE_DESK_TECHNICAL_ROLES),
        "users": list_users_for_admin(user),
    }


@frappe.whitelist(allow_guest=True)
def list_users():
    user = validate_service_request()
    return {"users": list_users_for_admin(user)}


@frappe.whitelist(allow_guest=True)
def create_user(payload):
    user = validate_service_request()
    return create_user_from_admin(_payload(payload), actor=user)


@frappe.whitelist(allow_guest=True)
def assign_roles(target_user: str, roles, primary_department: str = ""):
    user = validate_service_request()
    if isinstance(roles, str):
        roles = frappe.parse_json(roles)
    return update_user_roles(target_user, roles, primary_department, actor=user)


@frappe.whitelist(allow_guest=True)
def set_user_enabled(target_user: str, enabled: int):
    user = validate_service_request()
    if int(enabled):
        frappe.throw("Re-enable user is not implemented in this phase.", frappe.PermissionError)
    return disable_user(target_user, actor=user)


@frappe.whitelist(allow_guest=True)
def get_my_profile():
    user = validate_service_request()
    return get_current_profile(user)


@frappe.whitelist(allow_guest=True)
def update_my_profile(payload):
    user = validate_service_request()
    return update_current_profile(_payload(payload), user)


@frappe.whitelist(allow_guest=True)
def list_security_events(limit: int = 50):
    user = validate_service_request()
    roles = set(frappe.get_roles(user))
    if not roles & {"BEDO Security Auditor", "BEDO System Administrator", "BEDO User Administrator"}:
        frappe.throw("You do not have access to BEDO security logs.", frappe.PermissionError)
    rows = frappe.get_all(
        "BEDO Security Event",
        fields=["event_type", "username", "user", "status", "ip_address", "user_agent", "message", "created_at"],
        order_by="created_at desc",
        limit_page_length=min(int(limit or 50), 200),
    )
    return {"events": rows}
