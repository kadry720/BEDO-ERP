import frappe

from bedo_erp.shared.constants import (
    BEDO_DEPARTMENT_MANAGER_ROLE,
    BEDO_GM_ROLE,
    BEDO_SYSTEM_ADMIN_ROLE,
    FRAPPE_SYSTEM_ROLES,
    PHASE_1_ADMIN_READ_ROLES,
)


def get_current_user():
    return getattr(frappe.session, "user", None) or "Guest"


def get_roles(user=None):
    user = user or get_current_user()
    if user == "Guest":
        return []
    if user == "Administrator":
        return ["Administrator", "System Manager", BEDO_SYSTEM_ADMIN_ROLE]
    return frappe.get_roles(user)


def has_any_role(user, role_names):
    roles = set(get_roles(user))
    return bool(roles.intersection(set(role_names)))


def is_system_admin(user=None):
    user = user or get_current_user()
    if user == "Administrator":
        return True
    return has_any_role(user, (BEDO_SYSTEM_ADMIN_ROLE, *FRAPPE_SYSTEM_ROLES))


def is_admin_reader(user=None):
    user = user or get_current_user()
    if is_system_admin(user):
        return True
    return has_any_role(user, PHASE_1_ADMIN_READ_ROLES)


def is_department_manager(user=None):
    user = user or get_current_user()
    return has_any_role(user, (BEDO_DEPARTMENT_MANAGER_ROLE,))


def require_logged_in():
    if get_current_user() == "Guest":
        _deny("Login is required.")


def require_system_admin():
    require_logged_in()
    if not is_system_admin():
        _deny("BEDO System Admin access is required.")


def require_admin_read():
    require_logged_in()
    if not is_admin_reader():
        _deny("BEDO admin read access is required.")


def require_self_or_admin(target_user):
    require_logged_in()
    current_user = get_current_user()
    if current_user == target_user or is_admin_reader(current_user):
        return
    if is_department_manager(current_user) and users_share_department(current_user, target_user):
        return
    _deny("You are not allowed to access this user profile.")


def require_active_bedo_profile(user=None):
    user = user or get_current_user()
    require_logged_in()
    if is_system_admin(user):
        return
    settings = get_security_settings_document()
    if not settings.get("require_active_bedo_profile"):
        return
    profile = get_bedo_profile(user)
    if not profile or not profile.get("is_active_in_bedo_erp"):
        _deny("An active BEDO User Profile is required.")


def get_bedo_profile(user):
    if not user or user == "Guest":
        return None
    return frappe.db.get_value(
        "BEDO User Profile",
        {"user": user},
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


def users_share_department(left_user, right_user):
    left_department = frappe.db.get_value("BEDO User Profile", {"user": left_user}, "department")
    right_department = frappe.db.get_value("BEDO User Profile", {"user": right_user}, "department")
    return bool(left_department and right_department and left_department == right_department)


def get_security_settings_document():
    try:
        return frappe.get_single("BEDO Security Settings")
    except Exception:
        return frappe._dict(
            {
                "require_active_bedo_profile": 1,
                "enable_audit_logging": 1,
            }
        )


def assert_user_exists(user):
    if not user or not frappe.db.exists("User", user):
        frappe.throw("User does not exist.", frappe.DoesNotExistError)


def _deny(message):
    try:
        from bedo_erp.audit.services import write_permission_denied

        write_permission_denied(message)
    except Exception:
        pass
    frappe.throw(message, frappe.PermissionError)
