from __future__ import annotations

import frappe

from bedo_platform.services.profile_service import get_current_profile as get_profile
from bedo_platform.services.profile_service import update_current_profile as update_profile


@frappe.whitelist()
def get_current_profile():
    return get_profile()


@frappe.whitelist()
def update_current_profile(payload):
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    return update_profile(payload)
