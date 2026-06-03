from urllib.parse import urlparse
import socket

import frappe

from bedo_erp.identity.validators import validate_bedo_role
from bedo_erp.security.policies import get_current_user, require_logged_in, require_system_admin


def test_ldap_configuration():
    require_system_admin()
    settings = _get_ldap_settings()
    if not settings:
        return {
            "configured": False,
            "enabled": False,
            "reachable": False,
            "message": "Frappe LDAP Settings were not found.",
            "checks": {},
        }
    server_url = _first_setting(settings, "ldap_server_url", "server_url", "ldap_server")
    checks = {
        "server_url_configured": bool(server_url),
        "base_dn_configured": bool(_first_setting(settings, "base_dn", "ldap_search_path", "search_path")),
        "user_search_configured": bool(_first_setting(settings, "user_search_base", "ldap_search_string", "search_string")),
        "group_search_configured": bool(_first_setting(settings, "group_search_base", "ldap_group_field", "group_field")),
        "bind_user_configured": bool(_first_setting(settings, "ldap_bind_user", "bind_dn", "ldap_bind_dn")),
    }
    reachable = _can_reach_ldap_server(server_url)
    return {
        "configured": any(checks.values()),
        "enabled": bool(_first_setting(settings, "enabled", "enable_ldap")),
        "reachable": reachable,
        "message": "LDAP settings checked without exposing secrets.",
        "checks": checks,
    }


def sync_current_ldap_user_profile():
    require_logged_in()
    user = get_current_user()
    user_doc = frappe.get_doc("User", user)
    profile_name = frappe.db.get_value("BEDO User Profile", {"user": user}, "name")
    profile = frappe.get_doc("BEDO User Profile", profile_name) if profile_name else frappe.new_doc("BEDO User Profile")
    profile.user = user
    profile.full_name = user_doc.full_name
    profile.email = user_doc.email
    profile.auth_source = "LDAP"
    profile.ldap_username = user_doc.username or user_doc.email
    profile.is_created_from_ldap = 1
    profile.is_active_in_bedo_erp = 1
    profile.save(ignore_permissions=True)
    _assign_default_ldap_role(user)
    return {
        "profile": profile.name,
        "user": user,
        "auth_source": "LDAP",
        "is_active_in_bedo_erp": profile.is_active_in_bedo_erp,
    }


def apply_ldap_group_role_mappings(user, ldap_groups):
    if not ldap_groups:
        return []
    group_values = set(ldap_groups)
    mappings = frappe.get_all(
        "BEDO LDAP Group Role Mapping",
        filters={"is_active": 1},
        fields=["ldap_group_name", "ldap_group_dn", "frappe_role", "priority"],
        order_by="priority asc",
    )
    assigned_roles = []
    user_doc = frappe.get_doc("User", user)
    for mapping in mappings:
        if mapping.ldap_group_name not in group_values and mapping.ldap_group_dn not in group_values:
            continue
        validate_bedo_role(mapping.frappe_role)
        if mapping.frappe_role not in frappe.get_roles(user):
            user_doc.add_roles(mapping.frappe_role)
            assigned_roles.append(mapping.frappe_role)
    if assigned_roles:
        user_doc.save(ignore_permissions=True)
    return assigned_roles


def _assign_default_ldap_role(user):
    try:
        default_role = frappe.get_single("BEDO Security Settings").default_role_after_ldap_login
    except Exception:
        default_role = None
    if default_role:
        validate_bedo_role(default_role)
        user_doc = frappe.get_doc("User", user)
        if default_role not in frappe.get_roles(user):
            user_doc.add_roles(default_role)
            user_doc.save(ignore_permissions=True)


def _get_ldap_settings():
    if frappe.db.exists("DocType", "LDAP Settings"):
        try:
            return frappe.get_single("LDAP Settings")
        except Exception:
            return None
    return None


def _first_setting(doc, *fieldnames):
    for fieldname in fieldnames:
        if doc.meta.has_field(fieldname) and doc.get(fieldname):
            return doc.get(fieldname)
    return None


def _can_reach_ldap_server(server_url):
    if not server_url:
        return False
    parsed = urlparse(server_url)
    host = parsed.hostname or server_url
    port = parsed.port or (636 if parsed.scheme == "ldaps" else 389)
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError:
        return False
