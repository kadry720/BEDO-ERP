import sys
from types import ModuleType, SimpleNamespace

import pytest

from bedo_platform.services import profile_service


def install_fake_frappe(monkeypatch):
    class FakeUser:
        name = "gm@bedo.local"
        username = "gm"
        first_name = "General"
        middle_name = ""
        last_name = "Manager"
        email = "gm@bedo.local"
        phone = "+201000000000"
        enabled = 1
        flags = SimpleNamespace(ignore_permissions=False)

        def save(self, ignore_permissions=False):
            return None

    fake_frappe = ModuleType("frappe")
    fake_frappe.session = SimpleNamespace(user="gm@bedo.local")
    fake_frappe.PermissionError = type("PermissionError", (Exception,), {})
    fake_frappe.get_doc = lambda doctype, name=None: FakeUser()
    fake_frappe.throw = lambda message, exc=None: (_ for _ in ()).throw(exc(message) if exc else Exception(message))
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    monkeypatch.setattr(profile_service, "assert_user_can_login", lambda user: True)
    monkeypatch.setattr(profile_service, "ensure_user_profile", lambda *args, **kwargs: None)
    monkeypatch.setattr(profile_service, "log_security_event", lambda *args, **kwargs: None)


def base_payload(**overrides):
    payload = {
        "username": "gm",
        "first_name": "General",
        "last_name": "Manager",
        "email": "gm@bedo.local",
        "phone_number": "+201000000000",
    }
    payload.update(overrides)
    return payload


def test_profile_password_change_requires_current_password(monkeypatch):
    install_fake_frappe(monkeypatch)

    with pytest.raises(ValueError, match="Current password is required"):
        profile_service.update_current_profile(
            base_payload(new_password="BetterPassword123!", confirm_password="BetterPassword123!"),
            user="gm@bedo.local",
        )


def test_profile_password_change_requires_matching_confirmation(monkeypatch):
    install_fake_frappe(monkeypatch)

    with pytest.raises(ValueError, match="New password and confirmation must match"):
        profile_service.update_current_profile(
            base_payload(
                current_password="CurrentPassword123!",
                new_password="BetterPassword123!",
                confirm_password="DifferentPassword123!",
            ),
            user="gm@bedo.local",
        )
