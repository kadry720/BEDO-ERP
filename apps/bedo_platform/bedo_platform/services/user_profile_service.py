from __future__ import annotations

from datetime import datetime


def ensure_user_profile(user: str, username: str = "", *, active: bool = True, deleted: bool = False) -> None:
    import frappe

    if not user or user == "Guest":
        return
    existing = frappe.db.get_value("BEDO User Profile", {"user": user}, "name")
    doc = frappe.get_doc("BEDO User Profile", existing) if existing else frappe.new_doc("BEDO User Profile")
    next_active = 1 if active else 0
    next_deleted = 1 if deleted else 0
    changed = (
        not existing
        or doc.user != user
        or (doc.username or "") != (username or "")
        or int(doc.is_active_in_bedo_erp or 0) != next_active
        or int(doc.is_deleted or 0) != next_deleted
    )
    doc.user = user
    doc.username = username
    doc.is_active_in_bedo_erp = next_active
    doc.is_deleted = next_deleted
    if not deleted:
        if doc.deleted_at or doc.deleted_by:
            changed = True
            doc.deleted_at = None
            doc.deleted_by = None
    if existing and not changed:
        return
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def mark_user_deleted(user: str, deleted_by: str) -> None:
    import frappe

    username = frappe.db.get_value("User", user, "username") or user
    existing = frappe.db.get_value("BEDO User Profile", {"user": user}, "name")
    doc = frappe.get_doc("BEDO User Profile", existing) if existing else frappe.new_doc("BEDO User Profile")
    doc.user = user
    doc.username = username
    doc.is_active_in_bedo_erp = 0
    doc.is_deleted = 1
    doc.deleted_at = datetime.utcnow()
    doc.deleted_by = deleted_by
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def is_user_deleted(user: str) -> bool:
    import frappe

    if not user:
        return False
    profile = frappe.db.get_value(
        "BEDO User Profile",
        {"user": user},
        ["is_active_in_bedo_erp", "is_deleted"],
        as_dict=True,
    )
    if not profile:
        return False
    return bool(profile.is_deleted or not profile.is_active_in_bedo_erp)


def find_user_for_login(username: str, email: str = "") -> str:
    import frappe

    return (
        frappe.db.get_value("User", {"username": username}, "name")
        or (frappe.db.get_value("User", {"email": email}, "name") if email else "")
        or ""
    )


def assert_user_can_login(user: str) -> bool:
    import frappe

    if not user:
        return True
    enabled = frappe.db.get_value("User", user, "enabled")
    return bool(enabled) and not is_user_deleted(user)
