from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseUser:
    user: str
    username: str
    email: str


def authenticate_user(username: str, password: str) -> DatabaseUser | None:
    import frappe
    from frappe.utils.password import check_password

    from bedo_platform.services.user_profile_service import find_user_for_login

    user = find_user_for_login(username, f"{username}@bedo.local")
    if not user:
        return None
    try:
        check_password(user, password)
    except frappe.AuthenticationError:
        return None

    row = frappe.db.get_value("User", user, ["name", "username", "email"], as_dict=True) or {}
    return DatabaseUser(user=row.get("name") or user, username=row.get("username") or username, email=row.get("email") or "")


def set_user_password(user: str, password: str, *, logout_all_sessions: bool = False) -> None:
    if not user or not password:
        return
    from frappe.utils.password import update_password

    update_password(user, password, logout_all_sessions=logout_all_sessions)
