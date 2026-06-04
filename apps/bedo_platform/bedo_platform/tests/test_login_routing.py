from bedo_platform.constants import ACCESS_NOT_CONFIGURED_ROUTE
from bedo_platform.services.routing_service import resolve_landing_route


def test_general_manager_routes_to_gm_dashboard():
    route = resolve_landing_route(["BEDO Employee", "General Manager"], "GM_SUPPORT")

    assert route == "/gm"


def test_ard_manager_routes_to_ard_dashboard():
    route = resolve_landing_route(["BEDO Employee", "ARD User", "ARD Manager"], "ARD")

    assert route == "/ard"


def test_user_with_no_role_routes_to_access_not_configured():
    route = resolve_landing_route([], "")

    assert route == ACCESS_NOT_CONFIGURED_ROUTE
