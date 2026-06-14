from bedo_platform.constants import INITIAL_USERS, VISIBLE_BUSINESS_ROLE_NAMES


def test_visible_business_roles_match_srs_phase_allowlist():
    assert VISIBLE_BUSINESS_ROLE_NAMES == [
        "General Manager",
        "SRS Manager",
        "SRS Section Head",
        "SRS Team Leader",
        "SRS Engineer",
        "Command Center Representative",
    ]


def test_seed_users_include_srs_sections_and_no_visible_ard_roles():
    usernames = {user["username"] for user in INITIAL_USERS}

    assert "gm" in usernames
    assert "srsmanager" in usernames
    assert "srselectronicshead" in usernames
    assert "srsmechanicaldesigneng4" in usernames
    assert "commandcenter" in usernames
    assert "ardmanager" not in usernames
