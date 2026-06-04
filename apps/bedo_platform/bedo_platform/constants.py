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
        "dashboard_route": "/production",
        "is_global_access_department": 0,
    },
    {
        "key": "QC",
        "name": "Quality Control & Validation",
        "pillar_number": 6,
        "dashboard_route": "/qc",
        "is_global_access_department": 0,
    },
    {
        "key": "OPERATIONS",
        "name": "Operations",
        "pillar_number": 7,
        "dashboard_route": "/operations",
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
        "content": "GM Support Office Dashboard - placeholder",
    },
    {
        "page_name": "srs-dashboard",
        "title": "SRS Dashboard",
        "module": "SRS",
        "route": "/srs",
        "department_key": "SRS",
        "content": "SRS Dashboard - placeholder",
    },
    {
        "page_name": "ard-dashboard",
        "title": "ARD Main Dashboard",
        "module": "ARD",
        "route": "/ard",
        "department_key": "ARD",
        "content": "ARD Main Dashboard - placeholder",
    },
    {
        "page_name": "ard-blueprint-dashboard",
        "title": "ARD Blueprint Dashboard",
        "module": "ARD",
        "route": "/ard/blueprint",
        "department_key": "ARD",
        "content": "ARD Blueprint Phase Dashboard - placeholder",
    },
    {
        "page_name": "ard-validation-dashboard",
        "title": "ARD Validation Dashboard",
        "module": "ARD",
        "route": "/ard/validation",
        "department_key": "ARD",
        "content": "ARD Validation / Digital Breath Dashboard - placeholder",
    },
    {
        "page_name": "ard-scmdp-dashboard",
        "title": "ARD SCMDP Dashboard",
        "module": "ARD",
        "route": "/ard/scmdp",
        "department_key": "ARD",
        "content": "ARD SCMDP Dashboard - placeholder",
    },
    {
        "page_name": "ard-coordination-dashboard",
        "title": "ARD Coordination Dashboard",
        "module": "ARD",
        "route": "/ard/coordination",
        "department_key": "ARD",
        "content": "ARD Coordination Dashboard - placeholder",
    },
    {
        "page_name": "command-center-dashboard",
        "title": "Command Center Dashboard",
        "module": "Command Center",
        "route": "/command-center",
        "department_key": "COMMAND_CENTER",
        "content": "Command Center Dashboard - placeholder",
    },
    {
        "page_name": "production-dashboard",
        "title": "Production Dashboard",
        "module": "Production",
        "route": "/production",
        "department_key": "PRODUCTION",
        "content": "Production Dashboard - placeholder",
    },
    {
        "page_name": "qc-dashboard",
        "title": "QC Dashboard",
        "module": "QC",
        "route": "/qc",
        "department_key": "QC",
        "content": "QC Dashboard - placeholder",
    },
    {
        "page_name": "operations-dashboard",
        "title": "Operations Dashboard",
        "module": "Operations",
        "route": "/operations",
        "department_key": "OPERATIONS",
        "content": "Operations Dashboard - placeholder",
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

DEPARTMENT_ROLES = {
    "GM_SUPPORT": [
        "General Manager",
        "GM Support Office User",
        "GM Support Office Specialist",
        "GM Support Office Consultant",
    ],
    "SRS": [
        "SRS User",
        "SRS Manager",
        "SRS Deputy",
        "SRS Section Head",
        "SRS Team Leader",
        "SRS Senior Engineer",
        "SRS Research Fellow",
        "SRS External Consultant",
        "SRS Assistant",
    ],
    "ARD": [
        "ARD User",
        "ARD Manager",
        "ARD Deputy",
        "ARD Project Owner",
        "ARD Team Leader",
        "ARD Senior Engineer",
        "ARD Engineer",
        "ARD Software Engineer",
        "ARD AI and IoT Engineer",
        "ARD Electronics Engineer",
        "ARD Control Engineer",
        "ARD Electrical Power Engineer",
        "ARD Mechatronics Engineer",
        "ARD Mechanical Design Engineer",
        "ARD Mechanical Engineer",
        "ARD Documentation Specialist",
        "ARD Graphics and Art Specialist",
    ],
    "COMMAND_CENTER": [
        "Command Center User",
        "Command Center Manager",
        "Command Center Deputy",
        "Command Center Team Leader",
        "Command Center Senior Specialist",
        "Command Center Assistant",
        "Procurement and Sourcing Specialist",
        "Master Planning Specialist",
        "Kitting and Staging Specialist",
        "Inventory and ERP Control Specialist",
        "Technical Archiving and Support Specialist",
        "HSE and Safety Specialist",
        "Global Logistics and Export Specialist",
        "Knowledge Vault Archivist",
    ],
    "PRODUCTION": [
        "Production User",
        "Production Manager",
        "Production Deputy",
        "Production Vice Manager",
        "Production Admin Assistant",
        "Production Engineer",
        "Senior Production Engineer Metal",
        "Senior Production Engineer Assembly",
        "Senior Production Engineer Electronics",
        "Hall Supervisor",
        "Quality Supervisor",
        "Metal Fabrication Supervisor",
        "Metal Fabrication Quality Supervisor",
        "Mechanical Installation Supervisor",
        "Mechanical Assembly Supervisor",
        "Electrical Installation Supervisor",
        "Electronics Installation Supervisor",
        "Senior CNC and Laser Technician",
        "Senior Welding Technician",
        "Senior Painting Technician",
        "CNC Hall Specialist",
        "Assembly Unit Supervisor",
        "Senior Mechanical Assembly Technician",
        "Senior Electrical Technician",
        "Senior Electronics Technician",
        "Mechanical Installation Technician",
        "Mechanical and Electrical Assembly Technician",
        "Electronics and Soldering Lab Technician",
        "ERP Material Controller",
        "Kitting and Supply Technician",
    ],
    "QC": [
        "QC User",
        "QC Sector Manager",
        "Assistant QC Manager",
        "Product Line QC Leader",
        "Senior QC and Validation Engineer",
        "Aesthetic and UX Branding Auditor",
        "Remote Support Specialist",
    ],
    "OPERATIONS": [
        "Operations User",
        "Operations Manager",
        "Operations Deputy",
        "Project Coordinator",
        "Field Team Leader",
        "Technical Support Team Member",
        "Technical Support Specialist",
    ],
    "PURCHASING": [
        "Purchasing User",
        "Purchasing Manager",
        "Purchasing Specialist",
        "Supplier Relations Specialist",
    ],
    "HR": [
        "HR User",
        "HR Manager",
        "HR Specialist",
        "KPI Administrator",
    ],
    "IT_ADMINISTRATION": [
        "IT User",
        "IT Administrator",
        "LDAP Administrator",
    ],
}

ARD_TEAM_OPTIONS = [
    "Software Engineering Team",
    "AI & IoT Integration Team",
    "Electronics Engineering Team",
    "Control Engineering Team",
    "Electrical Power Team",
    "Mechatronics Team",
    "Mechanical Design Team",
    "Mechanical Engineering Team",
    "Documentation Team",
    "Graphics and Art Team",
]

GLOBAL_VIEW_ROLES = {
    "General Manager",
    "GM Support Office User",
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
    "GM Support Office User",
    "BEDO Security Auditor",
    "BEDO System Administrator",
}


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
        "description": "BEDO platform role.",
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
                    any(
                        token in role_name
                        for token in [
                            "Manager",
                            "Deputy",
                            "General Manager",
                            "Section Head",
                            "Team Leader",
                            "Supervisor",
                            "Vice Manager",
                        ]
                    )
                ),
                "is_active": 1,
                "description": f"{DEPARTMENT_BY_KEY[department_key]['name']} role.",
            }
        )

ALL_ROLE_NAMES = [role["role_name"] for role in ROLE_CATALOG]
ROLE_DEPARTMENT_KEY = {
    role["role_name"]: role["department_key"]
    for role in ROLE_CATALOG
    if role["department_key"]
}

INITIAL_USERS = [
    {
        "username": "gm",
        "first_name": "General",
        "last_name": "Manager",
        "email": "gm@bedo.local",
        "phone_number": "+0000000000",
        "primary_department": "GM_SUPPORT",
        "roles": [
            "BEDO Employee",
            "General Manager",
            "GM Support Office User",
            "BEDO Global Viewer",
            "BEDO User Administrator",
        ],
        "password_env": "BEDO_SEED_GM_PASSWORD",
    },
    {
        "username": "ard.manager",
        "first_name": "ARD",
        "last_name": "Manager",
        "email": "ard.manager@bedo.local",
        "phone_number": "+0000000001",
        "primary_department": "ARD",
        "roles": ["BEDO Employee", "ARD User", "ARD Manager"],
        "password_env": "BEDO_SEED_ARD_MANAGER_PASSWORD",
    },
]
