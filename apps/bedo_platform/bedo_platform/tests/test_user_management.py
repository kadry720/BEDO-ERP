import pytest

from bedo_platform.services.user_management_service import validate_user_payload


def test_create_user_validates_required_fields():
    payload = {
        "username": "new.user",
        "password": "temporary-ldap-password",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@bedo.local",
        "phone_number": "+201000000000",
        "primary_department": "ARD",
        "roles": ["BEDO Employee", "ARD User"],
    }

    result = validate_user_payload(payload, creating=True)

    assert result["username"] == "new.user"
    assert result["password"] == "temporary-ldap-password"


def test_create_user_rejects_invalid_phone():
    payload = {
        "username": "new.user",
        "password": "temporary-ldap-password",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@bedo.local",
        "phone_number": "bad",
        "primary_department": "ARD",
        "roles": ["BEDO Employee", "ARD User"],
    }

    with pytest.raises(ValueError):
        validate_user_payload(payload, creating=True)


def test_create_user_rejects_unknown_roles():
    payload = {
        "username": "new.user",
        "password": "temporary-ldap-password",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@bedo.local",
        "phone_number": "+201000000000",
        "primary_department": "ARD",
        "roles": ["BEDO Employee", "Unexpected Role"],
    }

    with pytest.raises(ValueError):
        validate_user_payload(payload, creating=True)
