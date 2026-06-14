from __future__ import annotations


def user_query_conditions(user: str | None = None) -> str:
    import frappe

    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    return f"`tabUser`.name = {frappe.db.escape(user)}"


def user_has_permission(doc, user: str | None = None) -> bool | None:
    import frappe

    user = user or frappe.session.user
    if user == "Administrator":
        return True
    return doc.name == user
