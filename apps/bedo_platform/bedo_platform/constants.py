from __future__ import annotations

ACCESS_NOT_CONFIGURED_ROUTE = "/access-not-configured"
ADMIN_USERS_ROUTE = "/admin/users"
PROFILE_ROUTE = "/profile"
FORBIDDEN_ROUTE = "/forbidden"

DEPARTMENTS = [
    {
        "key": "GM_SUPPORT",
        "name": "GM Support Office",
        "pillar_number": 1,
        "dashboard_route": "/gm",
        "is_global_access_department": 1,
    },
    {
        "key": "SRS",
        "name": "Strategic R&D Sector",
        "pillar_number": 2,
        "dashboard_route": "/srs",
        "is_global_access_department": 0,
    },
    {
        "key": "ARD",
        "name": "Applied R&D Department",
        "pillar_number": 3,
        "dashboard_route": "/ard",
        "is_global_access_department": 0,
    },
    {
        "key": "COMMAND_CENTER",
        "name": "Command Center",
        "pillar_number": 4,
        "dashboard_route": "/command-center",
        "is_global_access_department": 0,
    },
    {
        "key": "PRODUCTION",
        "name": "Production",
        "pillar_number": 5,
        "dashboard_route": "",
        "is_global_access_department": 0,
    },
    {
        "key": "QC",
        "name": "Quality Control & Validation",
        "pillar_number": 6,
        "dashboard_route": "",
        "is_global_access_department": 0,
    },
    {
        "key": "OPERATIONS",
        "name": "Operations",
        "pillar_number": 7,
        "dashboard_route": "",
        "is_global_access_department": 0,
    },
    {
        "key": "PURCHASING",
        "name": "Purchasing",
        "pillar_number": 0,
        "dashboard_route": "",
        "is_global_access_department": 0,
    },
    {
        "key": "HR",
        "name": "HR",
        "pillar_number": 0,
        "dashboard_route": "",
        "is_global_access_department": 0,
    },
    {
        "key": "IT_ADMINISTRATION",
        "name": "IT Administration",
        "pillar_number": 0,
        "dashboard_route": "",
        "is_global_access_department": 0,
    },
]

VISIBLE_DEPARTMENT_KEYS = {"GM_SUPPORT", "SRS", "ARD", "COMMAND_CENTER"}
VISIBLE_DEPARTMENTS = [department for department in DEPARTMENTS if department["key"] in VISIBLE_DEPARTMENT_KEYS]

DEPARTMENT_BY_KEY = {department["key"]: department for department in DEPARTMENTS}
DEPARTMENT_ROUTE_BY_KEY = {
    department["key"]: department["dashboard_route"]
    for department in DEPARTMENTS
    if department["dashboard_route"]
}

DASHBOARDS = [
    {
        "page_name": "gm-support-dashboard",
        "title": "GM Support Office Dashboard",
        "module": "GM Support",
        "route": "/gm",
        "department_key": "GM_SUPPORT",
        "content": "GM Support Office Dashboard",
    },
    {
        "page_name": "srs-dashboard",
        "title": "SRS Dashboard",
        "module": "SRS",
        "route": "/srs",
        "department_key": "SRS",
        "content": "SRS Dashboard",
    },
    {
        "page_name": "command-center-dashboard",
        "title": "Command Center Dashboard",
        "module": "Command Center",
        "route": "/command-center",
        "department_key": "COMMAND_CENTER",
        "content": "Command Center Dashboard",
    },
    {
        "page_name": "ard-dashboard",
        "title": "ARD Dashboard",
        "module": "ARD",
        "route": "/ard",
        "department_key": "ARD",
        "content": "ARD Dashboard",
    },
    {
        "page_name": "bedo-admin-users",
        "title": "BEDO Admin Users",
        "module": "BEDO Core",
        "route": ADMIN_USERS_ROUTE,
        "department_key": "",
        "content": "BEDO user administration",
    },
    {
        "page_name": "access-not-configured",
        "title": "Access Not Configured",
        "module": "BEDO Core",
        "route": ACCESS_NOT_CONFIGURED_ROUTE,
        "department_key": "",
        "content": "Access is not configured for this account. Contact a BEDO administrator.",
    },
]

BASE_PLATFORM_ROLES = [
    "BEDO Employee",
    "BEDO User Administrator",
    "BEDO Security Auditor",
    "BEDO System Administrator",
    "BEDO Global Viewer",
]

SRS_ELECTRONICS_SECTION_HEAD_ROLE = "SRS Electronics Section Head"

VISIBLE_BUSINESS_ROLES = [
    "General Manager",
    "SRS Manager",
    "SRS Section Head",
    SRS_ELECTRONICS_SECTION_HEAD_ROLE,
    "SRS Team Leader",
    "SRS Engineer",
    "Command Center Representative",
    "ARD Manager",
    "ARD Section Head",
    "ARD Team Leader",
    "ARD Engineer",
]

DEPARTMENT_ROLES = {
    "GM_SUPPORT": ["General Manager"],
    "SRS": [
        "SRS Manager",
        "SRS Section Head",
        "SRS Team Leader",
        "SRS Engineer",
    ],
    "COMMAND_CENTER": ["Command Center Representative"],
    "ARD": [
        "ARD Manager",
        "ARD Section Head",
        "ARD Team Leader",
        "ARD Engineer",
    ],
}

SRS_SECTION_OPTIONS = [
    "Electronics",
    "Electrical",
    "Control",
    "Mechatronics",
    "Mechanical",
    "Mechanical Design",
]

GLOBAL_VIEW_ROLES = {
    "BEDO Global Viewer",
}
ADMIN_ACCESS_ROLES = {
    "BEDO User Administrator",
    "BEDO System Administrator",
}
FRAPPE_DESK_TECHNICAL_ROLES = {
    "BEDO System Administrator",
}
SECURITY_AUDIT_ROLES = {
    "General Manager",
    "BEDO User Administrator",
    "BEDO Security Auditor",
    "BEDO System Administrator",
}
PROTECTED_SYSTEM_USERNAMES = {
    "administrator",
    "systemadmin",
    "useradmin",
    "securityauditor",
    "globalviewer",
}

SRS_ROLES = {"SRS Manager", "SRS Section Head", "SRS Team Leader", "SRS Engineer"}
COMMAND_CENTER_ROLES = {"Command Center Representative"}
ARD_ROLES = {"ARD Manager", "ARD Section Head", "ARD Team Leader", "ARD Engineer"}
SRS_PROJECT_OWNER_ELIGIBLE_ROLES = SRS_ROLES | {"General Manager"}
SRS_TEAM_MEMBER_ELIGIBLE_ROLES = SRS_ROLES


def _role_key(role_name: str) -> str:
    return role_name.upper().replace("&", "AND").replace("/", " ").replace("-", " ").replace(" ", "_")


ROLE_CATALOG = [
    {
        "role_key": _role_key(role_name),
        "role_name": role_name,
        "frappe_role": role_name,
        "department_key": "",
        "role_category": "Platform",
        "is_managerial": int("Administrator" in role_name or "Global Viewer" in role_name),
        "is_active": 1,
        "description": "Internal BEDO platform role.",
    }
    for role_name in BASE_PLATFORM_ROLES
]

ROLE_CATALOG.append(
    {
        "role_key": _role_key(SRS_ELECTRONICS_SECTION_HEAD_ROLE),
        "role_name": SRS_ELECTRONICS_SECTION_HEAD_ROLE,
        "frappe_role": SRS_ELECTRONICS_SECTION_HEAD_ROLE,
        "department_key": "",
        "role_category": "Capability",
        "is_managerial": 0,
        "is_active": 1,
        "description": "Capability role for SRS Electronics heads handling ARD electronics interruption cases.",
    }
)

for department_key, role_names in DEPARTMENT_ROLES.items():
    for role_name in role_names:
        ROLE_CATALOG.append(
            {
                "role_key": _role_key(role_name),
                "role_name": role_name,
                "frappe_role": role_name,
                "department_key": department_key,
                "role_category": "Department",
                "is_managerial": int(
                    role_name in {
                        "General Manager",
                        "SRS Manager",
                        "SRS Section Head",
                        "SRS Team Leader",
                        "ARD Manager",
                        "ARD Section Head",
                        "ARD Team Leader",
                    }
                ),
                "is_active": 1,
                "description": f"{DEPARTMENT_BY_KEY[department_key]['name']} role.",
            }
        )

ALL_ROLE_NAMES = [role["role_name"] for role in ROLE_CATALOG]
VISIBLE_BUSINESS_ROLE_NAMES = list(VISIBLE_BUSINESS_ROLES)
ROLE_DEPARTMENT_KEY = {
    role["role_name"]: role["department_key"]
    for role in ROLE_CATALOG
    if role["department_key"]
}

SEED_DEFAULT_PASSWORD_ENV = "BEDO_SEED_DEFAULT_PASSWORD"


def _seed_password_env(username: str) -> str:
    safe = "".join(char if char.isalnum() else "_" for char in username.upper())
    return f"BEDO_SEED_{safe}_PASSWORD"


def _user(
    username: str,
    first_name: str,
    last_name: str,
    department: str,
    roles: list[str],
    phone_index: int,
    *,
    internal_roles: list[str] | None = None,
    force_active: bool = False,
) -> dict[str, object]:
    return {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": f"{username}@bedo.local",
        "phone_number": f"+2000000{phone_index:04d}",
        "primary_department": department,
        "roles": ["BEDO Employee", *(internal_roles or []), *roles],
        "password_env": _seed_password_env(username),
        "force_active": force_active,
    }


INITIAL_USERS = [
    _user(
        "gm",
        "General",
        "Manager",
        "GM_SUPPORT",
        ["General Manager"],
        1,
        internal_roles=["BEDO User Administrator", "BEDO Security Auditor", "BEDO Global Viewer"],
        force_active=True,
    ),
    _user("systemadmin", "System", "Admin", "", [], 2, internal_roles=["BEDO System Administrator", "BEDO User Administrator", "BEDO Security Auditor"]),
    _user("useradmin", "User", "Admin", "", [], 3, internal_roles=["BEDO User Administrator"]),
    _user("securityauditor", "Security", "Auditor", "", [], 4, internal_roles=["BEDO Security Auditor"]),
    _user("globalviewer", "Global", "Viewer", "GM_SUPPORT", [], 5, internal_roles=["BEDO Global Viewer"]),
    _user("srsmanager", "SRS", "Manager", "SRS", ["SRS Manager"], 6),
    _user("commandcenter", "Command Center", "Representative", "COMMAND_CENTER", ["Command Center Representative"], 7),
]

for command_center_index in range(1, 5):
    INITIAL_USERS.append(
        _user(
            f"commandcenterrep{command_center_index}",
            "Command Center",
            f"Representative {command_center_index}",
            "COMMAND_CENTER",
            ["Command Center Representative"],
            70 + command_center_index,
        )
    )

INITIAL_USERS.extend(
    [
        _user("ardmanager", "ARD", "Manager", "ARD", ["ARD Manager"], 200, force_active=True),
        _user("ardsectionhead1", "ARD", "Section Head 1", "ARD", ["ARD Section Head"], 201, force_active=True),
        _user("ardsectionhead2", "ARD", "Section Head 2", "ARD", ["ARD Section Head"], 202, force_active=True),
        _user("ardteamleader1", "ARD", "Team Leader 1", "ARD", ["ARD Team Leader"], 203, force_active=True),
        _user("ardteamleader2", "ARD", "Team Leader 2", "ARD", ["ARD Team Leader"], 204, force_active=True),
        _user("ardengineer1", "ARD", "Engineer 1", "ARD", ["ARD Engineer"], 205, force_active=True),
        _user("ardengineer2", "ARD", "Engineer 2", "ARD", ["ARD Engineer"], 206, force_active=True),
        _user("ardengineer3", "ARD", "Engineer 3", "ARD", ["ARD Engineer"], 207, force_active=True),
        _user("ardengineer4", "ARD", "Engineer 4", "ARD", ["ARD Engineer"], 208, force_active=True),
    ]
)

_SRS_SECTION_USER_PREFIX = {
    "Electronics": "srselectronics",
    "Electrical": "srselectrical",
    "Control": "srscontrol",
    "Mechatronics": "srsmechatronics",
    "Mechanical": "srsmechanical",
    "Mechanical Design": "srsmechanicaldesign",
}

for section_index, section_name in enumerate(SRS_SECTION_OPTIONS, start=1):
    prefix = _SRS_SECTION_USER_PREFIX[section_name]
    phone_base = 100 + section_index * 10
    INITIAL_USERS.append(
        _user(
            f"{prefix}head",
            "SRS",
            f"{section_name} Section Head",
            "SRS",
            ["SRS Section Head", SRS_ELECTRONICS_SECTION_HEAD_ROLE] if section_name == "Electronics" else ["SRS Section Head"],
            phone_base,
        )
    )
    INITIAL_USERS.append(
        _user(
            f"{prefix}tl",
            "SRS",
            f"{section_name} Team Leader",
            "SRS",
            ["SRS Team Leader"],
            phone_base + 1,
        )
    )
    for engineer_index in range(1, 5):
        INITIAL_USERS.append(
            _user(
                f"{prefix}eng{engineer_index}",
                "SRS",
                f"{section_name} Engineer {engineer_index}",
                "SRS",
                ["SRS Engineer"],
                phone_base + 1 + engineer_index,
            )
        )

LEGACY_PHASE_USERNAMES = {
    "ard.manager",
}

SRS_WORKFLOW_TYPE = "SRS"
COMMAND_CENTER_WORKFLOW_TYPE = "COMMAND_CENTER"
SUPPLIERS_WORKFLOW_TYPE = "SUPPLIERS"
GLOBAL_DEADLINE_EXTENSION_APPROVAL = "GLOBAL_DEADLINE_EXTENSION_APPROVAL"
COMMAND_CENTER_SRS_ARD_GM_APPROVAL = "COMMAND_CENTER_SRS_ARD_GM_APPROVAL"
SUPPLIER_DEADLINE_EXTENSION_APPROVAL = "SUPPLIER_DEADLINE_EXTENSION_APPROVAL"

SRS_NODE_PRODUCT_DIGITAL_RELEASE = "PRODUCT_DIGITAL_RELEASE"
SRS_NODE_GATEWAY = "SRS_GATEWAY"
SRS_NODE_COORDINATION = "MANDATORY_COORDINATION_MEETING"
SRS_NODE_DELIVERABLES = "DELIVERABLES_MATRIX"
SRS_NODE_CASES_1_2 = "CASES_1_2"
SRS_NODE_CASES_3_4 = "CASES_3_4"
SRS_NODE_GM_APPROVAL = "GM_APPROVAL"
SRS_NODE_MANAGER_APPROVAL = "GATE_1_SRS_MANAGER_APPROVAL"
SRS_NODE_DUAL_GATE_APPROVAL = "DUAL_GATE_APPROVAL"
SRS_NODE_DEADLINE_LOCKED = "DEADLINE_LOCKED_IN_ERP"
SRS_NODE_ACTION_PATHS = "ACTION_PATHS"
SRS_NODE_CASE_1 = "CASE_1"
SRS_NODE_CASE_2 = "CASE_2"
SRS_NODE_CASE_3 = "CASE_3"
SRS_NODE_CASE_4 = "CASE_4"
SRS_NODE_GATE_2_PMDP = "GATE_2_PMDP"
SRS_NODE_PMDP_DUAL_GATE_APPROVAL = "PMDP_DUAL_GATE_APPROVAL"
SRS_NODE_PHYSICAL_BUILD_TEST = "PHYSICAL_BUILD_TEST"
SRS_NODE_EXTENSION_DEADLINE = "EXTENSION_DEADLINE"
SRS_NODE_SRS_DIRECTOR_APPROVAL = "SRS_DIRECTOR_APPROVAL"
SRS_NODE_PMDP = "PMDP"
SRS_NODE_BMDP = "BMDP"
SRS_NODE_COMMAND_CENTER_APPROVAL = "COMMAND_CENTER_APPROVAL"
SRS_NODE_FINAL_GM_APPROVAL = "FINAL_GM_APPROVAL"

SRS_FUNCTIONAL_NODES = [
    SRS_NODE_PRODUCT_DIGITAL_RELEASE,
    SRS_NODE_GATEWAY,
    SRS_NODE_COORDINATION,
    SRS_NODE_DELIVERABLES,
    SRS_NODE_CASES_1_2,
    SRS_NODE_CASES_3_4,
    SRS_NODE_GM_APPROVAL,
    SRS_NODE_MANAGER_APPROVAL,
    SRS_NODE_DUAL_GATE_APPROVAL,
    SRS_NODE_DEADLINE_LOCKED,
    SRS_NODE_ACTION_PATHS,
    SRS_NODE_CASE_1,
    SRS_NODE_CASE_2,
    SRS_NODE_CASE_3,
    SRS_NODE_CASE_4,
    SRS_NODE_GATE_2_PMDP,
    SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
    SRS_NODE_PHYSICAL_BUILD_TEST,
    SRS_NODE_EXTENSION_DEADLINE,
    SRS_NODE_SRS_DIRECTOR_APPROVAL,
    SRS_NODE_PMDP,
    SRS_NODE_BMDP,
]

SRS_PLACEHOLDER_NODES: list[str] = []

NODE_STATUS_LOCKED = "LOCKED"
NODE_STATUS_READY = "READY"
NODE_STATUS_IN_PROGRESS = "IN_PROGRESS"
NODE_STATUS_WAITING_APPROVAL = "WAITING_APPROVAL"
NODE_STATUS_COMPLETED = "COMPLETED"
NODE_STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
NODE_STATUS_OVERDUE = "OVERDUE"
NODE_STATUS_SKIPPED = "SKIPPED"

CASE_CLASSIFICATIONS = [
    "Case 1 - Legacy Validation",
    "Case 2 - Standard Innovation",
    "Case 3 - Experimental Prototyping",
    "Case 4 - Vanguard Manufacturing",
]
GM_APPROVAL_CASES = {
    "Case 3 - Experimental Prototyping",
    "Case 4 - Vanguard Manufacturing",
}
