import frappe


@frappe.whitelist()
def get_placeholder_text():
    return "BEDO Admin Dashboard Placeholder - UI owned by Zeinab"
