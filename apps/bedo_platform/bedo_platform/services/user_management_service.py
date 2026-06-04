from __future__ import annotations

import re
from typing import Any

from bedo_platform.constants import ADMIN_ACCESS_ROLES, ALL_ROLE_NAMES
from bedo_platform.services.auth_service import USERNAME_RE
from bedo_platform.services.ldap_service import LDAPUser, provision_user
from bedo_platform.services.security_audit_service import log_security_event

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s().-]{5,24}$")


def require_user_admin(user: str | None = None) -> None:
    import frappe

    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if not roles & ADMIN_ACCESS_ROLES:
        frappe.throw("You do not have access to BEDO user administration.", frappe.PermissionError)


def validate_user_payload(payload: dict[str, Any], *, creating: bool = True) -> dict[str, Any]:
    username = str(payload.get("username", "")).strip()
    if not USERNAME_RE.match(username):
        raise ValueError("Username is required and may contain only letters, numbers, dot, dash, and underscore.")
    password = str(payload.get("password", ""))
    if creating and not password:
        raise ValueError("Password is required for LDAP user creation.")
    first_name = str(payload.get("first_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()
    email = str(payload.get("email", "")).strip()
    phone_number = str(payload.get("phone_number", "")).strip()
    primary_department = str(payload.get("primary_department", "")).strip()
    roles = payload.get("roles") or []
    if isinstance(roles, str):
        roles = [role.strip() for role in roles.split(",") if role.strip()]

    if not first_name:
        raise ValueError("First name is required.")
    if not last_name:
        raise ValueError("Last name is required.")
    if not EMAIL_RE.match(email):
        raise ValueError("A valid email address is required.")
    if not PHONE_RE.match(phone_number):
        raise ValueError("A valid phone number is required.")
    if not roles:
        raise ValueError("At least one role is required.")
    unknown_roles = sorted(set(roles) - set(ALL_ROLE_NAMES))
    if unknown_roles:
        raise ValueError(f"Unknown roles: {', '.join(unknown_roles)}")
    if not primary_department and not set(roles).issubset({"BEDO User Administrator", "BEDO System Administrator"}):
        raise ValueError("Primary department is required unless this is a system admin-only user.")

    return {
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone_number,
        "primary_department": primary_department,
        "roles": roles,
    }


def _get_or_create_user(data: dict[str, Any]) -> str:
    import frappe

    existing = frappe.db.get_value("User", {"username": data["username"]}, "name")
    existing = existing or frappe.db.get_value("User", {"email": data["email"]}, "name")
    if existing:
        user_doc = frappe.get_doc("User", existing)
    else:
        user_doc = frappe.get_doc({"doctype": "User", "email": data["email"], "send_welcome_email": 0})

    user_doc.username = data["username"]
    user_doc.first_name = data["first_name"]
    user_doc.last_name = data["last_name"]
    user_doc.email = data["email"]
    user_doc.phone = data["phone_number"]
    user_doc.enabled = 1
    user_doc.flags.ignore_permissions = True
    user_doc.flags.no_reset_password = True
    if existing:
        user_doc.save(ignore_permissions=True)
    else:
        user_doc.insert(ignore_permissions=True)
    return user_doc.name


def _assign_roles(user: str, roles: list[str]) -> None:
    import frappe

    user_doc = frappe.get_doc("User", user)
    existing = {row.role for row in user_doc.roles}
    for role in roles:
        if role not in existing:
            user_doc.append("roles", {"role": role})
    user_doc.flags.ignore_permissions = True
    user_doc.save(ignore_permissions=True)


def _set_role_assignments(user: str, primary_department: str, roles: list[str]) -> None:
    import frappe

    for role_name in roles:
        role_catalog = frappe.db.get_value("BEDO Role Catalog", {"role_name": role_name}, "name")
        if not role_catalog:
            continue
        department = None
        if primary_department:
            department = frappe.db.get_value("BEDO Department", {"department_key": primary_department}, "name")
        existing = frappe.db.get_value(
            "BEDO User Role Assignment",
            {"user": user, "role_catalog": role_catalog},
            "name",
        )
        doc = frappe.get_doc("BEDO User Role Assignment", existing) if existing else frappe.new_doc("BEDO User Role Assignment")
        doc.user = user
        doc.department = department
        doc.role_catalog = role_catalog
        doc.is_primary_department = 1 if primary_department and role_name == roles[0] else 0
        doc.is_active = 1
        doc.flags.ignore_permissions = True
        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)


def create_user_from_admin(payload: dict[str, Any], actor: str | None = None) -> dict[str, Any]:
    require_user_admin(actor)
    data = validate_user_payload(payload, creating=True)

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
    log_security_event("user_creation", username=data["username"], user=actor or user, status="Success")
    return {"success": True, "user": user}


def update_user_roles(user: str, roles: list[str], primary_department: str = "", actor: str | None = None) -> dict[str, Any]:
    require_user_admin(actor)
    if not roles:
        raise ValueError("At least one role is required.")
    unknown_roles = sorted(set(roles) - set(ALL_ROLE_NAMES))
    if unknown_roles:
        raise ValueError(f"Unknown roles: {', '.join(unknown_roles)}")
    if not primary_department and not set(roles).issubset({"BEDO User Administrator", "BEDO System Administrator"}):
        raise ValueError("Primary department is required unless this is a system admin-only user.")
    _assign_roles(user, roles)
    _set_role_assignments(user, primary_department, roles)
    log_security_event("role_change", user=actor or user, status="Success", message=f"Target user: {user}")
    return {"success": True, "user": user}


def disable_user(user: str, actor: str | None = None) -> dict[str, Any]:
    require_user_admin(actor)
    import frappe

    user_doc = frappe.get_doc("User", user)
    user_doc.enabled = 0
    user_doc.flags.ignore_permissions = True
    user_doc.save(ignore_permissions=True)
    log_security_event("user_disablement", user=actor or user, status="Success", message=f"Target user: {user}")
    return {"success": True, "user": user}


def list_users_for_admin(actor: str | None = None) -> list[dict[str, Any]]:
    require_user_admin(actor)
    import frappe

    rows = frappe.get_all(
        "User",
        fields=["name", "username", "first_name", "last_name", "email", "phone", "enabled"],
        order_by="first_name asc",
    )
    result = []
    for row in rows:
        if row.name == "Administrator":
            continue
        roles = frappe.get_roles(row.name)
        primary_department = frappe.db.get_value(
            "BEDO User Role Assignment",
            {"user": row.name, "is_primary_department": 1, "is_active": 1},
            "department",
        )
        primary_department_key = ""
        if primary_department:
            primary_department_key = frappe.db.get_value("BEDO Department", primary_department, "department_key") or ""
        result.append(
            {
                "user": row.name,
                "username": row.username,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "email": row.email,
                "phone_number": row.phone,
                "primary_department": primary_department_key,
                "roles": [role for role in roles if role in ALL_ROLE_NAMES],
                "enabled": row.enabled,
            }
        )
    return result
