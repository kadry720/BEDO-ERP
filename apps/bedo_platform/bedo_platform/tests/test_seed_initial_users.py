import sys
from types import ModuleType

from bedo_platform.constants import INITIAL_USERS, SEED_DEFAULT_PASSWORD_ENV
from bedo_platform.setup import seed_all, seed_initial_users
from bedo_platform.setup.seed_initial_users import _seed_password_for_user


def test_initial_users_do_not_embed_passwords():
    assert INITIAL_USERS
    assert all("password" not in user for user in INITIAL_USERS)
    assert all(user.get("password_env") for user in INITIAL_USERS)


def test_seed_password_requires_explicit_env(monkeypatch):
    for user in INITIAL_USERS:
        monkeypatch.delenv(str(user["password_env"]), raising=False)
    monkeypatch.delenv(SEED_DEFAULT_PASSWORD_ENV, raising=False)

    assert _seed_password_for_user(INITIAL_USERS[0]) == ""


def test_seed_password_uses_shared_explicit_env(monkeypatch):
    monkeypatch.setenv(SEED_DEFAULT_PASSWORD_ENV, "local-explicit")

    assert _seed_password_for_user(INITIAL_USERS[0]) == "local-explicit"


def test_seed_password_prefers_user_specific_env(monkeypatch):
    user = INITIAL_USERS[0]
    monkeypatch.setenv(SEED_DEFAULT_PASSWORD_ENV, "shared")
    monkeypatch.setenv(str(user["password_env"]), "specific")

    assert _seed_password_for_user(user) == "specific"


def install_fake_frappe(monkeypatch, existing_user: str = "gm@bedo.local"):
    calls = {"commits": 0, "warnings": []}

    class FakeDB:
        def get_value(self, doctype, filters=None, fieldname=None, **kwargs):
            if doctype == "User" and isinstance(filters, dict) and filters.get("username") == "gm":
                return existing_user
            if doctype == "User" and isinstance(filters, dict) and filters.get("email") == "gm@bedo.local":
                return existing_user
            return None

        def commit(self):
            calls["commits"] += 1

    class FakeLogger:
        def warning(self, message):
            calls["warnings"].append(message)

    fake_frappe = ModuleType("frappe")
    fake_frappe.db = FakeDB()
    fake_frappe.logger = lambda name: FakeLogger()
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    return calls


def install_fake_frappe_for_existing_ard_user(monkeypatch):
    calls = {
        "passwords": [],
        "assigned_roles": [],
        "assignments": [],
        "profiles": [],
        "saved_users": [],
        "deleted_users": [],
        "commits": 0,
        "warnings": [],
    }

    class FakeUser:
        def __init__(self, name):
            self.name = name
            self.enabled = 0
            self.flags = type("Flags", (), {})()

        def save(self, ignore_permissions=False):
            calls["saved_users"].append((self.name, self.enabled, ignore_permissions))

    class FakeDB:
        def get_value(self, doctype, filters=None, fieldname=None, **kwargs):
            if doctype == "User" and isinstance(filters, dict):
                if filters.get("username") == "ardmanager":
                    return "ardmanager@bedo.local"
                if filters.get("email") == "ardmanager@bedo.local":
                    return "ardmanager@bedo.local"
            return None

        def commit(self):
            calls["commits"] += 1

    class FakeLogger:
        def warning(self, message):
            calls["warnings"].append(message)

    fake_frappe = ModuleType("frappe")
    fake_frappe.db = FakeDB()
    fake_frappe.get_doc = lambda doctype, name=None: FakeUser(name)
    fake_frappe.logger = lambda name: FakeLogger()
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    monkeypatch.setattr(seed_initial_users, "set_user_password", lambda *args, **kwargs: calls["passwords"].append((args, kwargs)))
    monkeypatch.setattr(seed_initial_users, "_assign_roles", lambda *args, **kwargs: calls["assigned_roles"].append((args, kwargs)))
    monkeypatch.setattr(seed_initial_users, "_set_role_assignments", lambda *args, **kwargs: calls["assignments"].append((args, kwargs)))
    monkeypatch.setattr(seed_initial_users, "ensure_user_profile", lambda *args, **kwargs: calls["profiles"].append((args, kwargs)))
    monkeypatch.setattr(seed_initial_users, "mark_user_deleted", lambda *args, **kwargs: calls["deleted_users"].append((args, kwargs)))
    monkeypatch.setattr(seed_initial_users, "_get_or_create_user", lambda data: (_ for _ in ()).throw(AssertionError("existing ARD users must not be recreated")))
    return calls


def patch_single_seed_user(monkeypatch):
    user = {
        "username": "gm",
        "first_name": "Changed",
        "last_name": "Manager",
        "email": "gm@bedo.local",
        "phone_number": "+201000000000",
        "primary_department": "GM_SUPPORT",
        "roles": ["BEDO Employee", "General Manager"],
        "password_env": "BEDO_SEED_GM_PASSWORD",
    }
    monkeypatch.setattr(seed_initial_users, "INITIAL_USERS", [user])
    return user


def test_seed_all_does_not_reset_existing_user_password_without_force(monkeypatch):
    install_fake_frappe(monkeypatch)
    patch_single_seed_user(monkeypatch)
    monkeypatch.setenv("BEDO_SEED_GM_PASSWORD", "GeneratedSeedPassword123!")
    monkeypatch.delenv("BEDO_FORCE_SEED_PASSWORD_RESET", raising=False)
    password_calls = []
    monkeypatch.setattr(seed_initial_users, "set_user_password", lambda *args, **kwargs: password_calls.append((args, kwargs)))
    monkeypatch.setattr(seed_initial_users, "_assign_roles", lambda *args, **kwargs: None)
    monkeypatch.setattr(seed_initial_users, "_set_role_assignments", lambda *args, **kwargs: None)
    monkeypatch.setattr(seed_initial_users, "_get_or_create_user", lambda data: (_ for _ in ()).throw(AssertionError("existing users must not be rewritten")))
    monkeypatch.setattr(seed_all.site_state, "mark_setup_complete", lambda: None)
    monkeypatch.setattr(seed_all.seed_departments, "execute", lambda: None)
    monkeypatch.setattr(seed_all.seed_roles, "execute", lambda: None)
    monkeypatch.setattr(seed_all.seed_dashboards, "execute", lambda: None)
    monkeypatch.setattr(seed_all.seed_srs_phase, "execute", lambda: None)

    seed_all.execute()

    assert password_calls == []


def test_seed_all_preserves_existing_profile_fields(monkeypatch):
    install_fake_frappe(monkeypatch)
    patch_single_seed_user(monkeypatch)
    monkeypatch.setenv("BEDO_SEED_GM_PASSWORD", "GeneratedSeedPassword123!")
    monkeypatch.setattr(seed_initial_users, "_assign_roles", lambda *args, **kwargs: None)
    monkeypatch.setattr(seed_initial_users, "_set_role_assignments", lambda *args, **kwargs: None)
    monkeypatch.setattr(seed_initial_users, "_get_or_create_user", lambda data: (_ for _ in ()).throw(AssertionError("seed must not overwrite existing profile fields")))
    monkeypatch.setattr(seed_initial_users, "set_user_password", lambda *args, **kwargs: None)
    monkeypatch.setattr(seed_all.site_state, "mark_setup_complete", lambda: None)
    monkeypatch.setattr(seed_all.seed_departments, "execute", lambda: None)
    monkeypatch.setattr(seed_all.seed_roles, "execute", lambda: None)
    monkeypatch.setattr(seed_all.seed_dashboards, "execute", lambda: None)
    monkeypatch.setattr(seed_all.seed_srs_phase, "execute", lambda: None)

    seed_all.execute()


def test_force_seed_password_reset_must_be_explicit(monkeypatch):
    install_fake_frappe(monkeypatch)
    patch_single_seed_user(monkeypatch)
    monkeypatch.setenv("BEDO_SEED_GM_PASSWORD", "GeneratedSeedPassword123!")
    monkeypatch.setenv("BEDO_FORCE_SEED_PASSWORD_RESET", "1")
    password_calls = []
    monkeypatch.setattr(seed_initial_users, "set_user_password", lambda *args, **kwargs: password_calls.append((args, kwargs)))
    monkeypatch.setattr(seed_initial_users, "_assign_roles", lambda *args, **kwargs: None)
    monkeypatch.setattr(seed_initial_users, "_set_role_assignments", lambda *args, **kwargs: None)

    seed_initial_users.execute(strict=True)

    assert password_calls == [(("gm@bedo.local", "GeneratedSeedPassword123!"), {"logout_all_sessions": True})]


def test_existing_ard_seed_user_is_reactivated_without_password_reset(monkeypatch):
    calls = install_fake_frappe_for_existing_ard_user(monkeypatch)
    user = {
        "username": "ardmanager",
        "first_name": "ARD",
        "last_name": "Manager",
        "email": "ardmanager@bedo.local",
        "phone_number": "+201000000001",
        "primary_department": "ARD",
        "roles": ["BEDO Employee", "ARD Manager"],
        "password_env": "BEDO_SEED_ARDMANAGER_PASSWORD",
        "force_active": True,
    }
    monkeypatch.setattr(seed_initial_users, "INITIAL_USERS", [user])
    monkeypatch.setattr(seed_initial_users, "LEGACY_SEED_USERNAMES", set())
    monkeypatch.setenv("BEDO_SEED_DEFAULT_PASSWORD", "seed-default")
    monkeypatch.delenv("BEDO_FORCE_SEED_PASSWORD_RESET", raising=False)

    seed_initial_users.execute(strict=True)

    assert calls["passwords"] == []
    assert calls["saved_users"] == [("ardmanager@bedo.local", 1, True)]
    assert calls["profiles"] == [(("ardmanager@bedo.local", "ardmanager"), {"active": True, "deleted": False})]
    assert calls["deleted_users"] == []
