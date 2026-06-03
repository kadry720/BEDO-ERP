import frappe

from bedo_erp.audit.services import write_access_audit_log
from bedo_erp.security.policies import get_bedo_profile, get_current_user


def record_session_creation(login_manager=None):
    user = _resolve_user(login_manager)
    if not user or user == "Guest":
        return
    profile = get_bedo_profile(user)
    auth_source = profile.get("auth_source") if profile else "Unknown"
    write_access_audit_log("Login Success", user=user, auth_source=auth_source, success=1)
    _update_profile_login_time(user, "last_successful_login")


def record_login_failure(user=None, reason=None):
    write_access_audit_log(
        "Login Failure",
        user=user or "Guest",
        auth_source="Unknown",
        success=0,
        failure_reason=reason or "Login failed.",
    )
    if user and frappe.db.exists("BEDO User Profile", {"user": user}):
        _update_profile_login_time(user, "last_failed_login")


def record_logout(login_manager=None):
    user = _resolve_user(login_manager) or get_current_user()
    if not user or user == "Guest":
        return
    profile = get_bedo_profile(user)
    auth_source = profile.get("auth_source") if profile else "Unknown"
    write_access_audit_log("Logout", user=user, auth_source=auth_source, success=1)


def logout_current_user():
    user = get_current_user()
    record_logout()
    login_manager = getattr(frappe.local, "login_manager", None)
    if login_manager:
        login_manager.logout()
    return {"logged_out": True, "user": user}


def extend_bootinfo(bootinfo):
    try:
        from bedo_erp.identity.services import get_current_user_context

        bootinfo.bedo_user_context = get_current_user_context()
    except Exception:
        bootinfo.bedo_user_context = None


def _resolve_user(login_manager=None):
    if login_manager and getattr(login_manager, "user", None):
        return login_manager.user
    return get_current_user()


def _update_profile_login_time(user, fieldname):
    profile_name = frappe.db.get_value("BEDO User Profile", {"user": user}, "name")
    if profile_name:
        frappe.db.set_value("BEDO User Profile", profile_name, fieldname, frappe.utils.now_datetime())
