import frappe

from bedo_erp.identity.validators import normalize_user, validate_bedo_role, validate_department
from bedo_erp.security.policies import (
    get_bedo_profile,
    get_current_user,
    is_admin_reader,
    is_department_manager,
    require_active_bedo_profile,
    require_logged_in,
    require_self_or_admin,
    require_system_admin,
    users_share_department,
)


def get_users_summary():
    require_logged_in()
    require_active_bedo_profile()
    current_user = get_current_user()
    filters = {}
    if is_admin_reader(current_user):
        filters = {}
    elif is_department_manager(current_user):
        profile = get_bedo_profile(current_user)
        if not profile or not profile.get("department"):
            frappe.throw("Department Manager profile must have a department.", frappe.PermissionError)
        filters = {"department": profile.get("department")}
    else:
        frappe.throw("BEDO user summary access is not allowed.", frappe.PermissionError)
    rows = frappe.get_all(
        "BEDO User Profile",
        filters=filters,
        fields=[
            "name",
            "user",
            "full_name",
            "email",
            "employee_code",
            "department",
            "job_title",
            "auth_source",
            "is_active_in_bedo_erp",
            "last_successful_login",
            "last_failed_login",
        ],
        order_by="full_name asc",
    )
    for row in rows:
        row["frappe_user_enabled"] = frappe.db.get_value("User", row.user, "enabled")
        row["roles"] = frappe.get_roles(row.user)
    return rows


def get_user_profile(user):
    target_user = normalize_user(user)
    require_self_or_admin(target_user)
    require_active_bedo_profile()
    profile = frappe.db.get_value(
        "BEDO User Profile",
        {"user": target_user},
        [
            "name",
            "user",
            "full_name",
            "email",
            "employee_code",
            "department",
            "job_title",
            "auth_source",
            "ldap_username",
            "is_created_from_ldap",
            "is_active_in_bedo_erp",
            "last_successful_login",
            "last_failed_login",
        ],
        as_dict=True,
    )
    if not profile:
        frappe.throw("BEDO User Profile does not exist.", frappe.DoesNotExistError)
    profile["roles"] = frappe.get_roles(target_user)
    return profile


def update_user_department(user, department):
    require_system_admin()
    target_user = normalize_user(user)
    validate_department(department)
    profile = _get_or_create_profile(target_user)
    profile.department = department
    profile.save(ignore_permissions=True)
    return {"user": target_user, "department": department}


def assign_bedo_role(user, role):
    require_system_admin()
    target_user = normalize_user(user)
    validate_bedo_role(role)
    user_doc = frappe.get_doc("User", target_user)
    if role not in frappe.get_roles(target_user):
        user_doc.add_roles(role)
        user_doc.save(ignore_permissions=True)
    return {"user": target_user, "role": role, "assigned": True}


def deactivate_bedo_user(user):
    require_system_admin()
    target_user = normalize_user(user)
    profile = _get_or_create_profile(target_user)
    profile.is_active_in_bedo_erp = 0
    profile.save(ignore_permissions=True)
    return {"user": target_user, "is_active_in_bedo_erp": 0}


def can_view_department_user(target_user):
    current_user = get_current_user()
    if is_admin_reader(current_user):
        return True
    if is_department_manager(current_user):
        return users_share_department(current_user, target_user)
    return current_user == target_user


def _get_or_create_profile(user):
    profile_name = frappe.db.get_value("BEDO User Profile", {"user": user}, "name")
    if profile_name:
        return frappe.get_doc("BEDO User Profile", profile_name)
    user_doc = frappe.get_doc("User", user)
    profile = frappe.new_doc("BEDO User Profile")
    profile.user = user
    profile.full_name = user_doc.full_name
    profile.email = user_doc.email
    profile.auth_source = "Local"
    profile.is_active_in_bedo_erp = 1
    return profile
