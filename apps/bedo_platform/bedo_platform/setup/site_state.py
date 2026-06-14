from __future__ import annotations


def mark_setup_complete() -> None:
    import frappe
    from frappe.defaults import set_global_default

    if frappe.db.table_exists("Installed Application"):
        frappe.db.set_value(
            "Installed Application",
            {"app_name": "frappe"},
            "is_setup_complete",
            1,
            update_modified=False,
        )

    if frappe.db.table_exists("System Settings"):
        frappe.db.set_single_value("System Settings", "setup_complete", 1)

    set_global_default("setup_complete", "1")
    set_global_default("desktop:home_page", "workspace")
    hide_unused_workspaces()
    frappe.clear_cache()


def hide_unused_workspaces() -> None:
    import frappe

    if not frappe.db.table_exists("Workspace"):
        return

    for workspace in ["Website", "Tools", "Integrations", "Build"]:
        if not frappe.db.exists("Workspace", workspace):
            continue
        doc = frappe.get_doc("Workspace", workspace)
        doc.is_hidden = 1
        doc.public = 0
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
