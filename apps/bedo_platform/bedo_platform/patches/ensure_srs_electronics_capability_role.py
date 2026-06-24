from __future__ import annotations

from bedo_platform.constants import SRS_ELECTRONICS_SECTION_HEAD_ROLE
from bedo_platform.setup import seed_roles


def execute() -> None:
    import frappe

    seed_roles.execute()

    user = (
        frappe.db.get_value("User", {"username": "srselectronicshead"}, "name")
        or frappe.db.get_value("User", {"email": "srselectronicshead@bedo.local"}, "name")
    )
    if not user:
        frappe.db.commit()
        return

    user_doc = frappe.get_doc("User", user)
    if not any(row.role == SRS_ELECTRONICS_SECTION_HEAD_ROLE for row in user_doc.roles):
        user_doc.append("roles", {"role": SRS_ELECTRONICS_SECTION_HEAD_ROLE})
        user_doc.flags.ignore_permissions = True
        user_doc.flags.no_reset_password = True
        user_doc.save(ignore_permissions=True)

    role_catalog = frappe.db.get_value(
        "BEDO Role Catalog",
        {"role_name": SRS_ELECTRONICS_SECTION_HEAD_ROLE},
        "name",
    )
    if role_catalog:
        existing = frappe.db.get_value(
            "BEDO User Role Assignment",
            {"user": user, "role_catalog": role_catalog},
            "name",
        )
        doc = frappe.get_doc("BEDO User Role Assignment", existing) if existing else frappe.new_doc("BEDO User Role Assignment")
        doc.user = user
        doc.role_catalog = role_catalog
        doc.department = None
        doc.is_primary_department = 0
        doc.is_active = 1
        doc.flags.ignore_permissions = True
        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)

    frappe.db.commit()
