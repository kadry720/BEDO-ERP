from __future__ import annotations

from bedo_platform.constants import ALL_ROLE_NAMES, FRAPPE_DESK_TECHNICAL_ROLES, ROLE_CATALOG


def execute() -> None:
    import frappe

    allowed_roles = set(ALL_ROLE_NAMES)

    for role in ROLE_CATALOG:
        desk_access = 1 if role["frappe_role"] in FRAPPE_DESK_TECHNICAL_ROLES else 0
        if not frappe.db.exists("Role", role["frappe_role"]):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role["frappe_role"],
                    "desk_access": desk_access,
                    "disabled": 0,
                }
            ).insert(ignore_permissions=True)
        else:
            frappe.db.set_value(
                "Role",
                role["frappe_role"],
                {"desk_access": desk_access, "disabled": 0},
                update_modified=False,
            )

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

    legacy_catalog_roles = {
        row.frappe_role
        for row in frappe.get_all("BEDO Role Catalog", fields=["name", "role_name", "frappe_role"])
        if row.role_name not in allowed_roles and row.frappe_role
    }

    for role_name in legacy_catalog_roles:
        for user_name in frappe.get_all("User", pluck="name"):
            user_doc = frappe.get_doc("User", user_name)
            if not any(row.role == role_name for row in user_doc.roles):
                continue
            user_doc.set("roles", [{"role": row.role} for row in user_doc.roles if row.role != role_name])
            user_doc.flags.ignore_permissions = True
            user_doc.save(ignore_permissions=True)

        for catalog in frappe.get_all("BEDO Role Catalog", filters={"frappe_role": role_name}, pluck="name"):
            frappe.db.set_value("BEDO Role Catalog", catalog, "is_active", 0, update_modified=False)

        assignment_catalogs = frappe.get_all(
            "BEDO Role Catalog",
            filters={"frappe_role": role_name},
            pluck="name",
        )
        for catalog in assignment_catalogs:
            for assignment in frappe.get_all(
                "BEDO User Role Assignment",
                filters={"role_catalog": catalog, "is_active": 1},
                pluck="name",
            ):
                frappe.db.set_value("BEDO User Role Assignment", assignment, "is_active", 0, update_modified=False)

        if frappe.db.exists("Role", role_name) and not frappe.db.exists("Has Role", {"role": role_name}):
            try:
                frappe.delete_doc("Role", role_name, ignore_permissions=True)
            except Exception:
                frappe.db.set_value("Role", role_name, "disabled", 1, update_modified=False)
    frappe.db.commit()
