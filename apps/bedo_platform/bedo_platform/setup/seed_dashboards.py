from __future__ import annotations

from bedo_platform.constants import DASHBOARDS


def _upsert_workspace(dashboard: dict[str, str]) -> None:
    import frappe

    if dashboard["route"] == "/app/access-not-configured":
        return
    workspace_title = f"{dashboard['title']} Workspace"
    existing = frappe.db.exists("Workspace", workspace_title)
    doc = frappe.get_doc("Workspace", existing) if existing else frappe.new_doc("Workspace")
    doc.label = workspace_title
    doc.title = workspace_title
    doc.module = dashboard["module"]
    doc.public = 1
    doc.is_standard = 1
    doc.content = "[]"
    doc.sequence_id = 100
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def _upsert_module_access(dashboard: dict[str, str]) -> None:
    import frappe

    department_key = dashboard.get("department_key")
    if not department_key:
        return
    department = frappe.db.get_value("BEDO Department", {"department_key": department_key}, "name")
    if not department:
        return
    existing = frappe.db.get_value(
        "BEDO Module Access",
        {"department": department, "dashboard_route": dashboard["route"]},
        "name",
    )
    doc = frappe.get_doc("BEDO Module Access", existing) if existing else frappe.new_doc("BEDO Module Access")
    doc.department = department
    doc.dashboard_route = dashboard["route"]
    doc.is_active = 1
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def execute() -> None:
    import frappe

    for dashboard in DASHBOARDS:
        _upsert_workspace(dashboard)
        _upsert_module_access(dashboard)
    frappe.db.commit()
