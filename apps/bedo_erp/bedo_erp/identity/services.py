import frappe

from bedo_erp.security.policies import (
    get_bedo_profile,
    get_current_user,
    get_roles,
    is_admin_reader,
    is_department_manager,
    is_system_admin,
    require_active_bedo_profile,
    require_logged_in,
)
from bedo_erp.shared.constants import BEDO_VIEWER_ROLE


def get_current_user_context():
    require_logged_in()
    user = get_current_user()
    require_active_bedo_profile(user)
    roles = get_roles(user)
    profile = get_bedo_profile(user)
    return {
        "user": user,
        "full_name": _get_full_name(user, profile),
        "roles": roles,
        "department": profile.get("department") if profile else None,
        "auth_source": profile.get("auth_source") if profile else "Local",
        "is_active_in_bedo_erp": profile.get("is_active_in_bedo_erp") if profile else None,
        "permissions": get_permissions_summary(user, roles),
    }


def get_permissions_summary(user, roles=None):
    roles = roles or get_roles(user)
    role_set = set(roles)
    system_admin = is_system_admin(user)
    admin_reader = is_admin_reader(user)
    department_manager = is_department_manager(user)
    return {
        "can_manage_phase_1": system_admin,
        "can_view_users": admin_reader or department_manager,
        "can_view_audit_logs": admin_reader,
        "can_manage_security_settings": system_admin,
        "can_view_own_profile": user != "Guest",
        "can_access_placeholder_home": bool(role_set.intersection({BEDO_VIEWER_ROLE}) or user != "Guest"),
    }


def _get_full_name(user, profile):
    if profile and profile.get("full_name"):
        return profile.get("full_name")
    return frappe.db.get_value("User", user, "full_name")
