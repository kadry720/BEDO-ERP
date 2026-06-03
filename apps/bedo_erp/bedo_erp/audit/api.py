import frappe

from bedo_erp.audit.services import get_logs


@frappe.whitelist()
def get_access_audit_logs(filters=None):
    return get_logs(filters=filters)
