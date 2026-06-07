from __future__ import annotations

import os

from bedo_platform.constants import INITIAL_USERS, LEGACY_PHASE_USERNAMES
from bedo_platform.services.ldap_service import LDAPUser, provision_user
from bedo_platform.services.user_profile_service import mark_user_deleted
from bedo_platform.services.user_management_service import (
    _assign_roles,
    _get_or_create_user,
    _set_role_assignments,
)

LEGACY_SEED_USERNAMES = LEGACY_PHASE_USERNAMES


def execute(strict: bool = False) -> None:
    import frappe

    missing = [
        user["password_env"]
        for user in INITIAL_USERS
        if user.get("password_env") and not os.environ.get(user["password_env"])
    ]
    if missing:
        message = (
            "Initial BEDO LDAP seed users were not provisioned because these environment "
            f"variables are missing: {', '.join(missing)}"
        )
        if strict:
            raise RuntimeError(message)
        frappe.logger("bedo_platform").warning(message)
        return

    for user_data in INITIAL_USERS:
        data = dict(user_data)
        if data.get("password_env"):
            data["password"] = os.environ[data["password_env"]]
        ldap_user = LDAPUser(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone_number=data["phone_number"],
        )
        provision_user(ldap_user, data["password"])
        user = _get_or_create_user(data)
        _assign_roles(user, data["roles"])
        _set_role_assignments(user, data["primary_department"], data["roles"])

    for username in LEGACY_SEED_USERNAMES:
        legacy_user = frappe.db.get_value("User", {"username": username}, "name")
        if legacy_user and not frappe.db.get_value("BEDO User Profile", {"user": legacy_user, "is_deleted": 1}, "name"):
            user_doc = frappe.get_doc("User", legacy_user)
            user_doc.enabled = 0
            user_doc.flags.ignore_permissions = True
            user_doc.save(ignore_permissions=True)
            mark_user_deleted(legacy_user, "Administrator")
    frappe.db.commit()
