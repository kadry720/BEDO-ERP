from pathlib import Path

from bedo_platform.constants import INITIAL_USERS, VISIBLE_BUSINESS_ROLE_NAMES


def test_visible_business_roles_match_srs_phase_allowlist():
    assert VISIBLE_BUSINESS_ROLE_NAMES == [
        "General Manager",
        "SRS Manager",
        "SRS Section Head",
        "SRS Electronics Section Head",
        "SRS Team Leader",
        "SRS Engineer",
        "Command Center Representative",
        "ARD Manager",
        "ARD Section Head",
        "ARD Team Leader",
        "ARD Engineer",
    ]


def test_seed_users_include_srs_ard_and_command_center_accounts():
    usernames = {user["username"] for user in INITIAL_USERS}

    assert "gm" in usernames
    assert "srsmanager" in usernames
    assert "srselectronicshead" in usernames
    assert "srsmechanicaldesigneng4" in usernames
    assert "commandcenter" in usernames
    assert "commandcenterrep1" in usernames
    assert "commandcenterrep4" in usernames
    assert "ardmanager" in usernames
    assert "ardsectionhead1" in usernames
    assert "ardteamleader2" in usernames
    assert "ardengineer4" in usernames


def test_ard_seed_repair_patch_is_registered():
    patches = Path("apps/bedo_platform/bedo_platform/patches.txt").read_text(encoding="utf-8")

    assert "[pre_model_sync]" in patches
    assert "bedo_platform.patches.reactivate_ard_and_command_center_seed_users" in patches
    assert "[post_model_sync]" in patches
    assert "bedo_platform.patches.backfill_approval_departments" in patches


def test_ard_roles_and_permissions_repair_patch_is_registered():
    patches = Path("apps/bedo_platform/bedo_platform/patches.txt").read_text(encoding="utf-8")

    assert "bedo_platform.patches.ensure_ard_roles_and_permissions" in patches
