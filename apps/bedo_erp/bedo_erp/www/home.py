import frappe


def get_context(context):
    context.no_cache = 1
    context.current_user = frappe.session.user
    context.roles = frappe.get_roles(frappe.session.user) if frappe.session.user != "Guest" else []
    context.department = _get_department(frappe.session.user)
    context.placeholder_cards = ["Admin", "SRS", "ARD", "Reports"]
    return context


def _get_department(user):
    if not user or user == "Guest":
        return None
    return frappe.db.get_value("BEDO User Profile", {"user": user}, "department")
