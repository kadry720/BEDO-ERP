import frappe

from bedo_erp.security.services import get_settings, update_settings


@frappe.whitelist()
def get_security_settings():
    return get_settings()


@frappe.whitelist()
def update_security_settings(data):
    return update_settings(data)
