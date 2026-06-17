from __future__ import annotations

import os

from bedo_platform.constants import INITIAL_USERS, LEGACY_PHASE_USERNAMES, SEED_DEFAULT_PASSWORD_ENV
from bedo_platform.services.database_auth_service import set_user_password
from bedo_platform.services.user_profile_service import mark_user_deleted
from bedo_platform.services.user_management_service import (
    _assign_roles,
    _get_or_create_user,
    _set_role_assignments,
)

LEGACY_SEED_USERNAMES = LEGACY_PHASE_USERNAMES
FORCE_SEED_PASSWORD_RESET_ENV = "BEDO_FORCE_SEED_PASSWORD_RESET"


def _seed_password_for_user(user_data: dict[str, object]) -> str:
    password_env = str(user_data.get("password_env") or "")
    return os.environ.get(password_env, "") or os.environ.get(SEED_DEFAULT_PASSWORD_ENV, "")


def _force_seed_password_reset() -> bool:
    return os.environ.get(FORCE_SEED_PASSWORD_RESET_ENV, "").strip() == "1"


def _find_existing_seed_user(user_data: dict[str, object]) -> str:
    import frappe

    username = str(user_data.get("username") or "")
    email = str(user_data.get("email") or "")
    return (
        frappe.db.get_value("User", {"username": username}, "name")
        or frappe.db.get_value("User", {"email": email}, "name")
        or ""
    )


def execute(strict: bool = False) -> None:
    import frappe

    force_password_reset = _force_seed_password_reset()
    planned_users = []
    missing = []
    for user_data in INITIAL_USERS:
        data = dict(user_data)
        password = _seed_password_for_user(data)
        existing_user = _find_existing_seed_user(data)
        needs_seed_password = not existing_user or force_password_reset
        if needs_seed_password and data.get("password_env") and not password:
            missing.append(str(data["password_env"]))
        planned_users.append((data, password, existing_user, needs_seed_password))

    if missing:
        message = (
            "Initial BEDO seed users were not provisioned because these environment "
            f"variables are missing: {SEED_DEFAULT_PASSWORD_ENV} or per-user values ({', '.join(missing)})"
        )
        if strict:
            raise RuntimeError(message)
        frappe.logger("bedo_platform").warning(message)

    missing_set = set(missing)
    for data, password, existing_user, needs_seed_password in planned_users:
        if needs_seed_password and data.get("password_env") in missing_set:
            continue
        if existing_user:
            user = existing_user
        else:
            data["password"] = password
            user = _get_or_create_user(data)
        if needs_seed_password and password:
            set_user_password(user, password, logout_all_sessions=True)
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
