from __future__ import annotations

from bedo_platform.constants import DEPARTMENTS


def execute() -> None:
    import frappe

    for department in DEPARTMENTS:
        existing = frappe.db.get_value(
            "BEDO Department",
            {"department_key": department["key"]},
            "name",
        )
        doc = frappe.get_doc("BEDO Department", existing) if existing else frappe.new_doc("BEDO Department")
        doc.department_key = department["key"]
        doc.department_name = department["name"]
        doc.pillar_number = department["pillar_number"]
        doc.dashboard_route = department["dashboard_route"]
        doc.is_active = 1
        doc.is_global_access_department = department["is_global_access_department"]
        doc.flags.ignore_permissions = True
        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)
    frappe.db.commit()
