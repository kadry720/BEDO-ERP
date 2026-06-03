import frappe


@frappe.whitelist()
def get_current_user_context():
    from bedo_erp.identity.services import get_current_user_context as build_context

    return build_context()


@frappe.whitelist()
def test_ldap_configuration():
    from bedo_erp.identity.ldap_service import test_ldap_configuration as run_test

    return run_test()


@frappe.whitelist()
def sync_current_ldap_user_profile():
    from bedo_erp.identity.ldap_service import sync_current_ldap_user_profile as sync_profile

    return sync_profile()


@frappe.whitelist()
def logout_current_user():
    from bedo_erp.identity.session_service import logout_current_user as logout_user

    return logout_user()
