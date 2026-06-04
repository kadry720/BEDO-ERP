from bedo_platform.constants import ALL_ROLE_NAMES

app_name = "bedo_platform"
app_title = "BEDO Platform"
app_publisher = "BEDO"
app_description = "BEDO internal enterprise platform foundation"
app_email = "admin@bedo.local"
app_license = "Proprietary"

fixtures = [
    {
        "dt": "Role",
        "filters": [["role_name", "in", ALL_ROLE_NAMES]],
    },
    {
        "dt": "Workspace",
        "filters": [
            [
                "name",
                "in",
                [
                    "GM Support Office Dashboard",
                    "SRS Dashboard",
                    "ARD Main Dashboard",
                    "ARD Blueprint Dashboard",
                    "ARD Validation Dashboard",
                    "ARD SCMDP Dashboard",
                    "ARD Coordination Dashboard",
                    "Command Center Dashboard",
                    "Production Dashboard",
                    "QC Dashboard",
                    "Operations Dashboard",
                    "BEDO Admin Users",
                ],
            ]
        ],
    },
]

after_install = "bedo_platform.setup.seed_all.execute"
after_migrate = "bedo_platform.setup.seed_all.execute"
on_session_creation = "bedo_platform.services.auth_service.enforce_ldap_only_session"
on_logout = "bedo_platform.services.auth_service.record_logout"

app_include_js = [
    "/assets/bedo_platform/js/dashboard_page.js",
    "/assets/bedo_platform/js/admin_users.js",
]
app_include_css = ["/assets/bedo_platform/css/bedo_platform.css"]

website_route_rules = [{"from_route": "/login", "to_route": "login"}]
auth_hooks = ["bedo_platform.services.auth_service.ldap_request_auth_hook"]
