import pytest

from bedo_platform.services.user_management_service import is_protected_system_user_identifier, validate_user_payload


def test_create_user_validates_required_fields():
    payload = {
        "username": "new.user",
        "password": "temporary-db-password",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@bedo.local",
        "phone_number": "+201000000000",
        "primary_department": "SRS",
        "roles": ["SRS Engineer"],
    }

    result = validate_user_payload(payload, creating=True)

    assert result["username"] == "new.user"
    assert result["password"] == "temporary-db-password"


def test_create_user_rejects_invalid_phone():
    payload = {
        "username": "new.user",
        "password": "temporary-db-password",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@bedo.local",
        "phone_number": "bad",
        "primary_department": "SRS",
        "roles": ["SRS Engineer"],
    }

    with pytest.raises(ValueError):
        validate_user_payload(payload, creating=True)


def test_create_user_rejects_unknown_roles():
    payload = {
        "username": "new.user",
        "password": "temporary-db-password",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@bedo.local",
        "phone_number": "+201000000000",
        "primary_department": "SRS",
        "roles": ["Unexpected Role"],
    }

    with pytest.raises(ValueError):
        validate_user_payload(payload, creating=True)


def test_create_user_allows_any_password():
    payload = {
        "username": "new.user",
        "password": "x",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@bedo.local",
        "phone_number": "+201000000000",
        "primary_department": "SRS",
        "roles": ["SRS Engineer"],
    }

    result = validate_user_payload(payload, creating=True)

    assert result["password"] == "x"


def test_system_account_identifiers_are_protected():
    assert is_protected_system_user_identifier("systemadmin") is True
    assert is_protected_system_user_identifier("globalviewer") is True
    assert is_protected_system_user_identifier("normal.srs.user") is False
