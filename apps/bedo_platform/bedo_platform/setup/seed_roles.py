from __future__ import annotations

from bedo_platform.constants import ROLE_CATALOG


def execute() -> None:
    import frappe

    for role in ROLE_CATALOG:
        if not frappe.db.exists("Role", role["frappe_role"]):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role["frappe_role"],
                    "desk_access": 1,
                    "disabled": 0,
                }
            ).insert(ignore_permissions=True)

        department_name = None
        if role["department_key"]:
            department_name = frappe.db.get_value(
                "BEDO Department",
                {"department_key": role["department_key"]},
                "name",
            )

        existing = frappe.db.get_value(
            "BEDO Role Catalog",
            {"role_key": role["role_key"]},
            "name",
        )
        doc = frappe.get_doc("BEDO Role Catalog", existing) if existing else frappe.new_doc("BEDO Role Catalog")
        doc.role_key = role["role_key"]
        doc.role_name = role["role_name"]
        doc.frappe_role = role["frappe_role"]
        doc.department = department_name
        doc.role_category = role["role_category"]
        doc.is_managerial = role["is_managerial"]
        doc.is_active = role["is_active"]
        doc.description = role["description"]
        doc.flags.ignore_permissions = True
        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)
    frappe.db.commit()
