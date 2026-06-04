from __future__ import annotations

import frappe

from bedo_platform.services.routing_service import (
    ensure_dashboard_access as ensure_access,
    get_current_user_landing_route,
    get_visible_dashboards_for_user,
)


@frappe.whitelist()
def get_current_user_landing_route():
    return {"route": get_current_user_landing_route()}


@frappe.whitelist()
def get_visible_departments_for_current_user():
    dashboards = get_visible_dashboards_for_user()
    return {"dashboards": dashboards}


@frappe.whitelist()
def ensure_dashboard_access(route: str):
    return ensure_access(route)
