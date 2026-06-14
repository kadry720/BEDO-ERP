from bedo_platform.constants import ACCESS_NOT_CONFIGURED_ROUTE
from bedo_platform.services.routing_service import resolve_landing_route, route_allowed_for_roles


def test_general_manager_routes_to_gm_dashboard():
    route = resolve_landing_route(["BEDO Employee", "General Manager"], "GM_SUPPORT")

    assert route == "/gm"


def test_srs_manager_routes_to_srs_dashboard():
    route = resolve_landing_route(["BEDO Employee", "SRS Manager"], "SRS")

    assert route == "/srs"


def test_command_center_routes_to_command_center_dashboard():
    route = resolve_landing_route(["BEDO Employee", "Command Center Representative"], "COMMAND_CENTER")

    assert route == "/command-center"


def test_user_with_no_role_routes_to_access_not_configured():
    route = resolve_landing_route([], "")

    assert route == ACCESS_NOT_CONFIGURED_ROUTE


def test_plain_gm_cannot_access_non_gm_route():
    assert route_allowed_for_roles("/srs", ["BEDO Employee", "General Manager"]) is False


def test_global_viewer_can_access_visible_routes():
    assert route_allowed_for_roles("/srs", ["BEDO Employee", "BEDO Global Viewer"]) is True
    assert route_allowed_for_roles("/command-center", ["BEDO Employee", "BEDO Global Viewer"]) is True


def test_global_viewer_precedence_over_gm_restriction():
    roles = ["BEDO Employee", "General Manager", "BEDO Global Viewer"]

    assert route_allowed_for_roles("/srs", roles) is True
    assert route_allowed_for_roles("/command-center", roles) is True
