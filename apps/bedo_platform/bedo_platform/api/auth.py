from __future__ import annotations

import frappe

from bedo_platform.services.auth_service import login as ldap_login
from bedo_platform.services.routing_service import get_current_user_landing_route


@frappe.whitelist(allow_guest=True)
def login(username: str, password: str):
    return ldap_login(username, password)


@frappe.whitelist()
def get_current_user_landing_route():
    return {"route": get_current_user_landing_route()}
