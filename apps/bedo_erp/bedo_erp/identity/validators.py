import frappe

from bedo_erp.shared.constants import BEDO_ROLES


def validate_bedo_role(role):
    if role not in BEDO_ROLES:
        frappe.throw("Role is not a Phase 1 BEDO role.", frappe.ValidationError)
    if not frappe.db.exists("Role", role):
        frappe.throw("Role does not exist.", frappe.DoesNotExistError)


def validate_department(department):
    if department and not frappe.db.exists("BEDO Department", department):
        frappe.throw("Department does not exist.", frappe.DoesNotExistError)


def normalize_user(user):
    if not user:
        frappe.throw("User is required.", frappe.ValidationError)
    if not frappe.db.exists("User", user):
        frappe.throw("User does not exist.", frappe.DoesNotExistError)
    return user
