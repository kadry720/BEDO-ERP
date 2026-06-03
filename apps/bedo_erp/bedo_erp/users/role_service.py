import frappe

from bedo_erp.identity.validators import validate_bedo_role
from bedo_erp.security.policies import require_system_admin


def assign_role(user, role):
    require_system_admin()
    validate_bedo_role(role)
    user_doc = frappe.get_doc("User", user)
    if role not in frappe.get_roles(user):
        user_doc.add_roles(role)
        user_doc.save(ignore_permissions=True)
    return {"user": user, "role": role, "assigned": True}
