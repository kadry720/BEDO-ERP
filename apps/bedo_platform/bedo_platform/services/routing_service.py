from __future__ import annotations

from collections.abc import Iterable

from bedo_platform.constants import (
    ACCESS_NOT_CONFIGURED_ROUTE,
    ADMIN_ACCESS_ROLES,
    ADMIN_USERS_ROUTE,
    DASHBOARDS,
    DEPARTMENT_ROUTE_BY_KEY,
    GLOBAL_VIEW_ROLES,
    ROLE_DEPARTMENT_KEY,
    SECURITY_AUDIT_ROLES,
)

DASHBOARD_BY_ROUTE = {dashboard["route"]: dashboard for dashboard in DASHBOARDS}
DEPARTMENT_ROLES_BY_KEY: dict[str, set[str]] = {}
for role_name, department_key in ROLE_DEPARTMENT_KEY.items():
    DEPARTMENT_ROLES_BY_KEY.setdefault(department_key, set()).add(role_name)

ADMIN_SHELL_ROLES = ADMIN_ACCESS_ROLES | {"BEDO Security Auditor"}


def normalize_roles(role_names: Iterable[str] | None) -> set[str]:
    return {role for role in (role_names or []) if role}


def resolve_landing_route(
    role_names: Iterable[str] | None,
    primary_department: str | None = None,
) -> str:
    roles = normalize_roles(role_names)
    if roles & GLOBAL_VIEW_ROLES:
        return DEPARTMENT_ROUTE_BY_KEY["GM_SUPPORT"]
    if roles & ADMIN_SHELL_ROLES and not any_department_role(roles):
        return ADMIN_USERS_ROUTE
    if primary_department and primary_department in DEPARTMENT_ROUTE_BY_KEY:
        if roles_can_access_department(roles, primary_department):
            return DEPARTMENT_ROUTE_BY_KEY[primary_department]
    for department_key in ["SRS", "COMMAND_CENTER", "GM_SUPPORT"]:
        if roles_can_access_department(roles, department_key):
            return DEPARTMENT_ROUTE_BY_KEY[department_key]
    if roles & ADMIN_SHELL_ROLES:
        return ADMIN_USERS_ROUTE
    return ACCESS_NOT_CONFIGURED_ROUTE


def any_department_role(roles: set[str]) -> bool:
    return any(role in ROLE_DEPARTMENT_KEY for role in roles)


def roles_can_access_department(roles: Iterable[str], department_key: str) -> bool:
    role_set = normalize_roles(roles)
    return bool(role_set & DEPARTMENT_ROLES_BY_KEY.get(department_key, set()))


def route_allowed_for_roles(route: str, role_names: Iterable[str] | None) -> bool:
    roles = normalize_roles(role_names)
    if route == ADMIN_USERS_ROUTE:
        return bool(roles & ADMIN_SHELL_ROLES)
    dashboard = DASHBOARD_BY_ROUTE.get(route)
    if not dashboard:
        return route == ACCESS_NOT_CONFIGURED_ROUTE
    department_key = dashboard.get("department_key")
    if not department_key:
        return True
    if "BEDO Global Viewer" in roles:
        return True
    if "General Manager" in roles and department_key != "GM_SUPPORT":
        return False
    return roles_can_access_department(roles, department_key)


def get_user_roles(user: str | None = None) -> list[str]:
    import frappe

    user = user or frappe.session.user
    return frappe.get_roles(user)


def get_primary_department(user: str | None = None) -> str:
    import frappe

    user = user or frappe.session.user
    assignment = frappe.db.get_value(
        "BEDO User Role Assignment",
        {"user": user, "is_primary_department": 1, "is_active": 1},
        "department",
    )
    if not assignment:
        return ""
    return frappe.db.get_value("BEDO Department", assignment, "department_key") or ""


def get_current_user_landing_route(user: str | None = None) -> str:
    return resolve_landing_route(get_user_roles(user), get_primary_department(user))


def get_visible_dashboards_for_user(user: str | None = None) -> list[dict[str, str]]:
    roles = get_user_roles(user)
    return [
        dashboard
        for dashboard in DASHBOARDS
        if dashboard["route"] != ACCESS_NOT_CONFIGURED_ROUTE
        and route_allowed_for_roles(dashboard["route"], roles)
    ]


def ensure_dashboard_access(route: str, user: str | None = None) -> dict[str, object]:
    import frappe

    user = user or frappe.session.user
    roles = get_user_roles(user)
    allowed = route_allowed_for_roles(route, roles)
    if not allowed:
        frappe.throw("You do not have access to this BEDO dashboard.", frappe.PermissionError)
    dashboard = DASHBOARD_BY_ROUTE.get(route, {})
    return {
        "allowed": True,
        "route": route,
        "title": dashboard.get("title", ""),
        "content": dashboard.get("content", ""),
        "visible_dashboards": get_visible_dashboards_for_user(user),
    }
