from __future__ import annotations

import os

from bedo_platform.constants import INITIAL_USERS
from bedo_platform.services.user_management_service import (
    _assign_roles,
    _get_or_create_user,
    _set_role_assignments,
)


def execute(strict: bool = False) -> None:
    import frappe

    missing = [user["password_env"] for user in INITIAL_USERS if not os.environ.get(user["password_env"])]
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
        data["password"] = os.environ[data["password_env"]]
        user = _get_or_create_user(data)
        _assign_roles(user, data["roles"])
        _set_role_assignments(user, data["primary_department"], data["roles"])
    frappe.db.commit()
