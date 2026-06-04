from bedo_platform.services.routing_service import route_allowed_for_roles


def test_ard_user_cannot_open_srs_dashboard():
    assert route_allowed_for_roles("/app/srs-dashboard", ["BEDO Employee", "ARD User"]) is False


def test_srs_user_cannot_open_ard_dashboard():
    assert route_allowed_for_roles("/app/ard-dashboard", ["BEDO Employee", "SRS User"]) is False


def test_gm_can_open_all_department_dashboards():
    roles = ["BEDO Employee", "General Manager"]

    assert route_allowed_for_roles("/app/srs-dashboard", roles) is True
    assert route_allowed_for_roles("/app/ard-dashboard", roles) is True
    assert route_allowed_for_roles("/app/production-dashboard", roles) is True


def test_admin_dashboard_requires_admin_role():
    assert route_allowed_for_roles("/app/bedo-admin-users", ["BEDO Employee"]) is False
    assert route_allowed_for_roles("/app/bedo-admin-users", ["BEDO User Administrator"]) is True
