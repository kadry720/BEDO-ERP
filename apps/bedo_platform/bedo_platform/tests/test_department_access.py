from bedo_platform.services.routing_service import route_allowed_for_roles


def test_srs_user_can_open_srs_dashboard():
    assert route_allowed_for_roles("/srs", ["BEDO Employee", "SRS Engineer"]) is True


def test_platform_user_cannot_open_srs_dashboard():
    assert route_allowed_for_roles("/srs", ["BEDO Employee"]) is False


def test_gm_only_opens_gm_dashboard_not_general_srs_dashboard():
    roles = ["BEDO Employee", "General Manager"]

    assert route_allowed_for_roles("/gm", roles) is True
    assert route_allowed_for_roles("/srs", roles) is False


def test_admin_dashboard_requires_admin_role():
    assert route_allowed_for_roles("/admin/users", ["BEDO Employee"]) is False
    assert route_allowed_for_roles("/admin/users", ["General Manager"]) is False
    assert route_allowed_for_roles("/admin/users", ["BEDO User Administrator"]) is True
