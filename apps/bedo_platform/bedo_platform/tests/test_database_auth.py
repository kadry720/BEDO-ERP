import sys
from types import ModuleType, SimpleNamespace

from bedo_platform.services import database_auth_service


def install_fake_frappe(monkeypatch, fake_frappe, *, check_password=None, update_password=None):
    frappe_module = ModuleType("frappe")
    frappe_module.db = fake_frappe.db
    frappe_module.AuthenticationError = fake_frappe.AuthenticationError
    utils_module = ModuleType("frappe.utils")
    password_module = ModuleType("frappe.utils.password")
    password_module.check_password = check_password or (lambda user, password: None)
    password_module.update_password = update_password or (lambda user, password, logout_all_sessions=False: None)
    utils_module.password = password_module
    frappe_module.utils = utils_module
    monkeypatch.setitem(sys.modules, "frappe", frappe_module)
    monkeypatch.setitem(sys.modules, "frappe.utils", utils_module)
    monkeypatch.setitem(sys.modules, "frappe.utils.password", password_module)


def test_database_auth_uses_frappe_user_password(monkeypatch):
    calls = {}

    class FakeDB:
        def get_value(self, doctype, name, fields, as_dict=False):
            assert doctype == "User"
            assert name == "gm@bedo.local"
            assert as_dict is True
            return {"name": "gm@bedo.local", "username": "gm", "email": "gm@bedo.local"}

    fake_frappe = SimpleNamespace(
        db=FakeDB(),
        AuthenticationError=type("AuthenticationError", (Exception,), {}),
    )

    def fake_find_user_for_login(username, fallback_email):
        assert username == "gm"
        assert fallback_email == "gm@bedo.local"
        return "gm@bedo.local"

    def fake_check_password(user, password):
        calls["check_password"] = (user, password)

    install_fake_frappe(monkeypatch, fake_frappe, check_password=fake_check_password)
    monkeypatch.setattr("bedo_platform.services.user_profile_service.find_user_for_login", fake_find_user_for_login)

    user = database_auth_service.authenticate_user("gm", "secret")

    assert user is not None
    assert user.user == "gm@bedo.local"
    assert user.username == "gm"
    assert calls["check_password"] == ("gm@bedo.local", "secret")


def test_set_user_password_uses_frappe_password_store(monkeypatch):
    calls = {}

    def fake_update_password(user, password, logout_all_sessions=False):
        calls["update_password"] = (user, password, logout_all_sessions)

    fake_frappe = SimpleNamespace(
        db=SimpleNamespace(),
        AuthenticationError=type("AuthenticationError", (Exception,), {}),
    )
    install_fake_frappe(monkeypatch, fake_frappe, update_password=fake_update_password)

    database_auth_service.set_user_password("gm@bedo.local", "new-secret", logout_all_sessions=True)

    assert calls["update_password"] == ("gm@bedo.local", "new-secret", True)


def test_check_current_password_uses_frappe_password_store(monkeypatch):
    calls = {}
    fake_frappe = SimpleNamespace(
        db=SimpleNamespace(),
        AuthenticationError=type("AuthenticationError", (Exception,), {}),
    )

    def fake_check_password(user, password):
        calls["check_password"] = (user, password)

    install_fake_frappe(monkeypatch, fake_frappe, check_password=fake_check_password)

    assert database_auth_service.check_current_password("gm@bedo.local", "CurrentPassword123!") is True
    assert calls["check_password"] == ("gm@bedo.local", "CurrentPassword123!")


def test_check_current_password_returns_false_for_bad_password(monkeypatch):
    authentication_error = type("AuthenticationError", (Exception,), {})
    fake_frappe = SimpleNamespace(
        db=SimpleNamespace(),
        AuthenticationError=authentication_error,
    )

    def fake_check_password(user, password):
        raise authentication_error()

    install_fake_frappe(monkeypatch, fake_frappe, check_password=fake_check_password)

    assert database_auth_service.check_current_password("gm@bedo.local", "wrong") is False


def test_password_policy_allows_common_passwords():
    errors = database_auth_service.validate_password_policy(
        "password",
        username="gm",
        email="gm@bedo.local",
        first_name="General",
        last_name="Manager",
    )

    assert errors == []


def test_password_policy_allows_identity_substrings():
    errors = database_auth_service.validate_password_policy(
        "gm",
        username="gm",
        email="gm@bedo.local",
        first_name="General",
        last_name="Manager",
    )

    assert errors == []


def test_password_policy_accepts_strong_password():
    errors = database_auth_service.validate_password_policy(
        "CorrectHorseBattery!47",
        username="gm",
        email="gm@bedo.local",
        first_name="General",
        last_name="Manager",
    )

    assert errors == []
