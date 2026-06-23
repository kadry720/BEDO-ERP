from __future__ import annotations


def execute() -> None:
    import frappe
    from bedo_platform.services.project_service import _approval_department_for_type

    rows = frappe.get_all(
        "SRS Approval",
        fields=["name", "approval_type", "approval_department"],
    )
    for row in rows:
        if row.approval_department:
            continue
        frappe.db.set_value(
            "SRS Approval",
            row.name,
            "approval_department",
            _approval_department_for_type(row.approval_type),
            update_modified=False,
        )
    frappe.db.commit()
