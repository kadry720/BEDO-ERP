app_name = "bedo_erp"
app_title = "BEDO ERP"
app_publisher = "BEDO"
app_description = "BEDO ERP Phase 1 authentication and administration foundation"
app_email = "admin@example.local"
app_license = "Proprietary"

fixtures = [
    {
        "dt": "Role",
        "filters": [
            [
                "role_name",
                "in",
                [
                    "BEDO System Admin",
                    "BEDO GM",
                    "BEDO SRS Manager",
                    "BEDO ARD Manager",
                    "BEDO Department Manager",
                    "BEDO Engineer",
                    "BEDO Viewer",
                ],
            ]
        ],
    },
    "Custom Field",
    "Property Setter",
    {
        "dt": "Workspace",
        "filters": [["name", "=", "BEDO Admin Dashboard"]],
    },
]

after_install = "bedo_erp.patches.seed_phase_1_data.execute"
after_migrate = "bedo_erp.patches.seed_phase_1_data.execute"
on_session_creation = "bedo_erp.identity.session_service.record_session_creation"
on_logout = "bedo_erp.identity.session_service.record_logout"
boot_session = "bedo_erp.identity.session_service.extend_bootinfo"

website_route_rules = [
    {"from_route": "/bedo", "to_route": "home"},
]
