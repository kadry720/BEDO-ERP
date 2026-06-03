BEDO_ROLES = (
    "BEDO System Admin",
    "BEDO GM",
    "BEDO SRS Manager",
    "BEDO ARD Manager",
    "BEDO Department Manager",
    "BEDO Engineer",
    "BEDO Viewer",
)

BEDO_SYSTEM_ADMIN_ROLE = "BEDO System Admin"
BEDO_GM_ROLE = "BEDO GM"
BEDO_DEPARTMENT_MANAGER_ROLE = "BEDO Department Manager"
BEDO_ENGINEER_ROLE = "BEDO Engineer"
BEDO_VIEWER_ROLE = "BEDO Viewer"

FRAPPE_SYSTEM_ROLES = ("System Manager", "Administrator")
PHASE_1_ADMIN_READ_ROLES = (BEDO_SYSTEM_ADMIN_ROLE, BEDO_GM_ROLE, "System Manager")

AUTH_SOURCES = ("Local", "LDAP", "Unknown")
USER_PROFILE_AUTH_SOURCES = ("Local", "LDAP")

AUDIT_EVENT_TYPES = (
    "Login Success",
    "Login Failure",
    "Logout",
    "Session Expired",
    "Permission Denied",
)

DEFAULT_DEPARTMENTS = (
    ("GM", "GM Office"),
    ("SRS", "SRS"),
    ("ARD", "ARD"),
    ("COMMAND_CENTER", "Command Center"),
    ("PRODUCTION", "Production"),
    ("QC", "QC"),
    ("OPERATIONS", "Operations"),
)

SECURITY_SETTINGS_DEFAULTS = {
    "enable_ldap_login": 0,
    "allow_local_login_for_system_admin": 1,
    "allow_local_login_for_normal_users": 0,
    "max_failed_login_attempts": 5,
    "lockout_duration_minutes": 15,
    "session_timeout_minutes": 120,
    "require_active_bedo_profile": 1,
    "enable_audit_logging": 1,
}

SECURITY_SETTINGS_FIELDS = (
    "enable_ldap_login",
    "allow_local_login_for_system_admin",
    "allow_local_login_for_normal_users",
    "default_role_after_ldap_login",
    "max_failed_login_attempts",
    "lockout_duration_minutes",
    "session_timeout_minutes",
    "require_active_bedo_profile",
    "enable_audit_logging",
)
