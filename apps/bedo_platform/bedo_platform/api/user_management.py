from __future__ import annotations

import frappe

from bedo_platform.constants import ALL_ROLE_NAMES, DEPARTMENTS
from bedo_platform.services.user_management_service import (
    create_user_from_admin as create_user,
    disable_user as disable_existing_user,
    list_users_for_admin as list_users,
    update_user_roles as update_roles,
)


@frappe.whitelist()
def get_admin_bootstrap():
    return {
        "roles": ALL_ROLE_NAMES,
        "departments": DEPARTMENTS,
        "users": list_users(),
    }


@frappe.whitelist()
def list_users_for_admin():
    return {"users": list_users()}


@frappe.whitelist()
def create_user_from_admin(payload):
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    return create_user(payload)


@frappe.whitelist()
def update_user_roles(user: str, roles, primary_department: str = ""):
    if isinstance(roles, str):
        roles = frappe.parse_json(roles)
    return update_roles(user, roles, primary_department)


@frappe.whitelist()
def disable_user(user: str):
    return disable_existing_user(user)
