import frappe


@frappe.whitelist()
def get_users_summary():
    from bedo_erp.users.services import get_users_summary as build_summary

    return build_summary()


@frappe.whitelist()
def get_user_profile(user):
    from bedo_erp.users.services import get_user_profile as read_profile

    return read_profile(user)


@frappe.whitelist()
def update_user_department(user, department):
    from bedo_erp.users.services import update_user_department as update_department

    return update_department(user, department)


@frappe.whitelist()
def assign_bedo_role(user, role):
    from bedo_erp.users.services import assign_bedo_role as assign_role

    return assign_role(user, role)


@frappe.whitelist()
def deactivate_bedo_user(user):
    from bedo_erp.users.services import deactivate_bedo_user as deactivate_user

    return deactivate_user(user)
