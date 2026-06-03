import frappe

from bedo_erp.shared.constants import BEDO_ROLES, DEFAULT_DEPARTMENTS, SECURITY_SETTINGS_DEFAULTS


def execute():
    ensure_roles()
    ensure_departments()
    ensure_security_settings()


def ensure_roles():
    for role in BEDO_ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role,
                    "desk_access": 1,
                    "is_custom": 1,
                }
            ).insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Role", role, "desk_access", 1)


def ensure_departments():
    for code, name in DEFAULT_DEPARTMENTS:
        if frappe.db.exists("BEDO Department", code):
            continue
        frappe.get_doc(
            {
                "doctype": "BEDO Department",
                "department_code": code,
                "department_name": name,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True)


def ensure_security_settings():
    doc = frappe.get_single("BEDO Security Settings")
    changed = False
    for fieldname, value in SECURITY_SETTINGS_DEFAULTS.items():
        if doc.get(fieldname) in (None, ""):
            doc.set(fieldname, value)
            changed = True
    if changed:
        doc.save(ignore_permissions=True)
