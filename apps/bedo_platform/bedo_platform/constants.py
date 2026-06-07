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
        "dashboard_route": "",
        "is_global_access_department": 0,
    },
    {
        "key": "COMMAND_CENTER",
        "name": "Command Center",
        "pillar_number": 4,
        "dashboard_route": "",
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

VISIBLE_DEPARTMENT_KEYS = {"GM_SUPPORT", "SRS"}
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

VISIBLE_BUSINESS_ROLES = [
    "General Manager",
    "SRS Manager",
    "SRS Section Head",
    "SRS Team Leader",
    "SRS Engineer",
]

DEPARTMENT_ROLES = {
    "GM_SUPPORT": ["General Manager"],
    "SRS": [
        "SRS Manager",
        "SRS Section Head",
        "SRS Team Leader",
        "SRS Engineer",
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
    "General Manager",
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

SRS_ROLES = {"SRS Manager", "SRS Section Head", "SRS Team Leader", "SRS Engineer"}
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
                    role_name in {"General Manager", "SRS Manager", "SRS Section Head", "SRS Team Leader"}
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

DEV_SEED_PASSWORD = "123456"


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
        "password": DEV_SEED_PASSWORD,
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
]

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
            ["SRS Section Head"],
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
    "ardmanager",
    "ardsectionhead1",
    "ardsectionhead2",
    "ardteamleader1",
    "ardteamleader2",
    "ardengineer1",
    "ardengineer2",
    "ardengineer3",
    "ardengineer4",
}

SRS_WORKFLOW_TYPE = "SRS"

SRS_NODE_PRODUCT_DIGITAL_RELEASE = "PRODUCT_DIGITAL_RELEASE"
SRS_NODE_GATEWAY = "SRS_GATEWAY"
SRS_NODE_COORDINATION = "MANDATORY_COORDINATION_MEETING"
SRS_NODE_DELIVERABLES = "DELIVERABLES_MATRIX"
SRS_NODE_CASES_1_2 = "CASES_1_2"
SRS_NODE_CASES_3_4 = "CASES_3_4"
SRS_NODE_GM_APPROVAL = "GM_APPROVAL"
SRS_NODE_MANAGER_APPROVAL = "GATE_1_SRS_MANAGER_APPROVAL"
SRS_NODE_DEADLINE_LOCKED = "DEADLINE_LOCKED_IN_ERP"
SRS_NODE_ACTION_PATHS = "ACTION_PATHS"
SRS_NODE_CASE_1 = "CASE_1"
SRS_NODE_CASE_2 = "CASE_2"
SRS_NODE_CASE_3 = "CASE_3"
SRS_NODE_CASE_4 = "CASE_4"
SRS_NODE_BMDP = "BMDP"

SRS_FUNCTIONAL_NODES = [
    SRS_NODE_PRODUCT_DIGITAL_RELEASE,
    SRS_NODE_GATEWAY,
    SRS_NODE_COORDINATION,
    SRS_NODE_DELIVERABLES,
    SRS_NODE_CASES_1_2,
    SRS_NODE_CASES_3_4,
    SRS_NODE_GM_APPROVAL,
    SRS_NODE_MANAGER_APPROVAL,
    SRS_NODE_DEADLINE_LOCKED,
    SRS_NODE_ACTION_PATHS,
    SRS_NODE_CASE_1,
    SRS_NODE_CASE_2,
    SRS_NODE_CASE_3,
    SRS_NODE_CASE_4,
    SRS_NODE_BMDP,
]

SRS_PLACEHOLDER_NODES: list[str] = []

NODE_STATUS_LOCKED = "LOCKED"
NODE_STATUS_READY = "READY"
NODE_STATUS_IN_PROGRESS = "IN_PROGRESS"
NODE_STATUS_WAITING_APPROVAL = "WAITING_APPROVAL"
NODE_STATUS_COMPLETED = "COMPLETED"
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
