import frappe

from bedo_erp.security.policies import require_admin_read, require_system_admin
from bedo_erp.shared.constants import SECURITY_SETTINGS_DEFAULTS, SECURITY_SETTINGS_FIELDS


def get_settings():
    require_admin_read()
    doc = _get_or_create_settings()
    return _serialize_settings(doc)


def update_settings(data):
    require_system_admin()
    payload = frappe.parse_json(data) if isinstance(data, str) else data
    if not isinstance(payload, dict):
        frappe.throw("Security settings payload must be an object.", frappe.ValidationError)
    doc = _get_or_create_settings()
    for fieldname in SECURITY_SETTINGS_FIELDS:
        if fieldname not in payload:
            continue
        doc.set(fieldname, _coerce_setting_value(fieldname, payload[fieldname]))
    doc.save(ignore_permissions=True)
    return _serialize_settings(doc)


def _get_or_create_settings():
    doc = frappe.get_single("BEDO Security Settings")
    changed = False
    for fieldname, value in SECURITY_SETTINGS_DEFAULTS.items():
        if doc.get(fieldname) in (None, ""):
            doc.set(fieldname, value)
            changed = True
    if changed:
        doc.save(ignore_permissions=True)
    return doc


def _coerce_setting_value(fieldname, value):
    if fieldname in {
        "enable_ldap_login",
        "allow_local_login_for_system_admin",
        "allow_local_login_for_normal_users",
        "require_active_bedo_profile",
        "enable_audit_logging",
    }:
        return 1 if frappe.utils.cint(value) else 0
    if fieldname in {
        "max_failed_login_attempts",
        "lockout_duration_minutes",
        "session_timeout_minutes",
    }:
        coerced = frappe.utils.cint(value)
        if coerced < 0:
            frappe.throw(f"{fieldname} cannot be negative.", frappe.ValidationError)
        return coerced
    if fieldname == "default_role_after_ldap_login" and value:
        if not frappe.db.exists("Role", value):
            frappe.throw("Default LDAP role does not exist.", frappe.DoesNotExistError)
    return value


def _serialize_settings(doc):
    return {fieldname: doc.get(fieldname) for fieldname in SECURITY_SETTINGS_FIELDS}
