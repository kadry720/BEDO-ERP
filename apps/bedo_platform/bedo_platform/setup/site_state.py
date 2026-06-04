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
    frappe.clear_cache()
