from __future__ import annotations

import re
from typing import Any

from bedo_platform.constants import (
    ADMIN_ACCESS_ROLES,
    ALL_ROLE_NAMES,
    PROTECTED_SYSTEM_USERNAMES,
    ROLE_DEPARTMENT_KEY,
    VISIBLE_BUSINESS_ROLE_NAMES,
)
from bedo_platform.services.auth_service import USERNAME_RE
from bedo_platform.services.ldap_service import LDAPUser, change_password, provision_user
from bedo_platform.services.security_audit_service import log_security_event
from bedo_platform.services.user_profile_service import ensure_user_profile, is_user_deleted, mark_user_deleted

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s().-]{5,24}$")


def _normalize_identifier(value: str | None) -> str:
    return str(value or "").strip().lower()


def is_protected_system_user_identifier(*values: str | None) -> bool:
    return any(_normalize_identifier(value) in PROTECTED_SYSTEM_USERNAMES for value in values if value)


def _is_protected_system_user(user: str) -> bool:
    import frappe

    row = frappe.db.get_value("User", user, ["name", "username", "email"], as_dict=True) or {}
    return is_protected_system_user_identifier(row.get("name"), row.get("username"), row.get("email"))


def _throw_if_protected_system_user(user: str) -> None:
    import frappe

    if _is_protected_system_user(user):
        frappe.throw("This system account is protected from normal user administration.", frappe.PermissionError)


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
    unknown_roles = sorted(set(roles) - set(VISIBLE_BUSINESS_ROLE_NAMES))
    if unknown_roles:
        raise ValueError(f"Unknown roles: {', '.join(unknown_roles)}")
    department_roles = {role for role in roles if role in ROLE_DEPARTMENT_KEY}
    if department_roles and not primary_department:
        raise ValueError("Primary department is required when assigning department roles.")

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


def _all_bedo_managed_roles() -> set[str]:
    import frappe

    catalog_roles = {
        row.frappe_role
        for row in frappe.get_all("BEDO Role Catalog", fields=["frappe_role"])
        if row.frappe_role
    }
    return catalog_roles | set(ALL_ROLE_NAMES)


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
    ensure_user_profile(user_doc.name, data["username"], active=True, deleted=False)
    return user_doc.name


def _assign_roles(user: str, roles: list[str]) -> None:
    import frappe

    user_doc = frappe.get_doc("User", user)
    managed_roles = _all_bedo_managed_roles()
    kept_rows = [{"role": row.role} for row in user_doc.roles if row.role not in managed_roles]
    user_doc.set("roles", kept_rows)
    existing = {row.role for row in user_doc.roles}
    roles_to_assign = ["BEDO Employee", *roles]
    for role in roles_to_assign:
        if role not in existing:
            user_doc.append("roles", {"role": role})
            existing.add(role)
    user_doc.flags.ignore_permissions = True
    user_doc.save(ignore_permissions=True)


def _set_role_assignments(user: str, primary_department: str, roles: list[str]) -> None:
    import frappe

    allowed_catalog_names = []
    roles_to_assign = ["BEDO Employee", *roles]
    for role_name in roles_to_assign:
        catalog_name = frappe.db.get_value("BEDO Role Catalog", {"role_name": role_name}, "name")
        if catalog_name:
            allowed_catalog_names.append(catalog_name)

    existing_assignments = frappe.get_all(
        "BEDO User Role Assignment",
        filters={"user": user, "is_active": 1},
        fields=["name", "role_catalog"],
    )
    for assignment in existing_assignments:
        if assignment.role_catalog not in allowed_catalog_names:
            frappe.db.set_value("BEDO User Role Assignment", assignment.name, "is_active", 0, update_modified=False)

    first_department_role = next((role for role in roles_to_assign if role in ROLE_DEPARTMENT_KEY), "")
    for role_name in roles_to_assign:
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
        doc.is_primary_department = 1 if primary_department and role_name == first_department_role else 0
        doc.is_active = 1
        doc.flags.ignore_permissions = True
        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)


def create_user_from_admin(payload: dict[str, Any], actor: str | None = None) -> dict[str, Any]:
    require_user_admin(actor)
    data = validate_user_payload(payload, creating=True)
    if is_protected_system_user_identifier(data["username"], data["email"]):
        raise ValueError("This username is reserved for a protected system account.")

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
    log_security_event("user_creation", username=data["username"], user=actor or user, target_user=user, status="Success")
    return {"success": True, "user": user}


def update_user_roles(user: str, roles: list[str], primary_department: str = "", actor: str | None = None) -> dict[str, Any]:
    require_user_admin(actor)
    _throw_if_protected_system_user(user)
    if not roles:
        raise ValueError("At least one role is required.")
    unknown_roles = sorted(set(roles) - set(VISIBLE_BUSINESS_ROLE_NAMES))
    if unknown_roles:
        raise ValueError(f"Unknown roles: {', '.join(unknown_roles)}")
    department_roles = {role for role in roles if role in ROLE_DEPARTMENT_KEY}
    if department_roles and not primary_department:
        raise ValueError("Primary department is required when assigning department roles.")
    _assign_roles(user, roles)
    _set_role_assignments(user, primary_department, roles)
    log_security_event("role_change", user=actor or user, target_user=user, status="Success")
    return {"success": True, "user": user}


def update_user_from_admin(user: str, payload: dict[str, Any], actor: str | None = None) -> dict[str, Any]:
    require_user_admin(actor)
    import frappe

    _throw_if_protected_system_user(user)
    if is_user_deleted(user):
        frappe.throw("Deleted users cannot be edited.", frappe.PermissionError)

    data = validate_user_payload(payload, creating=False)
    user_doc = frappe.get_doc("User", user)

    duplicate_username = frappe.db.get_value("User", {"username": data["username"]}, "name")
    if duplicate_username and duplicate_username != user:
        raise ValueError("Username is already in use.")
    duplicate_email = frappe.db.get_value("User", {"email": data["email"]}, "name")
    if duplicate_email and duplicate_email != user:
        raise ValueError("Email is already in use.")

    user_doc.username = data["username"]
    user_doc.first_name = data["first_name"]
    user_doc.last_name = data["last_name"]
    user_doc.email = data["email"]
    user_doc.phone = data["phone_number"]
    user_doc.enabled = 1
    user_doc.flags.ignore_permissions = True
    user_doc.flags.no_reset_password = True
    user_doc.save(ignore_permissions=True)

    if data["password"]:
        change_password(data["username"], data["password"])

    ensure_user_profile(user, data["username"], active=True, deleted=False)
    _assign_roles(user, data["roles"])
    _set_role_assignments(user, data["primary_department"], data["roles"])
    log_security_event("user_update", username=data["username"], user=actor or user, target_user=user, status="Success")
    return {"success": True, "user": user}


def soft_delete_user(user: str, actor: str | None = None) -> dict[str, Any]:
    require_user_admin(actor)
    import frappe

    actor = actor or frappe.session.user
    if user == actor:
        frappe.throw("You cannot delete your own BEDO account.", frappe.PermissionError)
    _throw_if_protected_system_user(user)

    user_doc = frappe.get_doc("User", user)
    user_doc.enabled = 0
    user_doc.flags.ignore_permissions = True
    user_doc.save(ignore_permissions=True)
    mark_user_deleted(user, actor)
    for assignment in frappe.get_all("BEDO User Role Assignment", filters={"user": user, "is_active": 1}, pluck="name"):
        frappe.db.set_value("BEDO User Role Assignment", assignment, "is_active", 0, update_modified=False)
    log_security_event("user_soft_delete", user=actor, target_user=user, status="Success")
    return {"success": True, "user": user}


def disable_user(user: str, actor: str | None = None) -> dict[str, Any]:
    return soft_delete_user(user, actor=actor)


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
        if row.name in {"Administrator", "Guest"} or is_user_deleted(row.name):
            continue
        if is_protected_system_user_identifier(row.name, row.username, row.email):
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
                "roles": [role for role in roles if role in VISIBLE_BUSINESS_ROLE_NAMES],
                "enabled": row.enabled,
                "can_delete": row.name != actor,
            }
        )
    return result
