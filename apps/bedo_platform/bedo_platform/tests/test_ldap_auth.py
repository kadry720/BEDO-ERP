from bedo_platform.services.ldap_service import authenticate


def test_mock_ldap_success(monkeypatch):
    monkeypatch.setenv("BEDO_LDAP_ADAPTER", "mock")
    monkeypatch.setenv("BEDO_MOCK_LDAP_PASSWORD_GM", "correct-password")

    user = authenticate("gm", "correct-password")

    assert user is not None
    assert user.username == "gm"
    assert user.email == "gm@bedo.local"


def test_mock_ldap_failed_auth(monkeypatch):
    monkeypatch.setenv("BEDO_LDAP_ADAPTER", "mock")
    monkeypatch.setenv("BEDO_MOCK_LDAP_PASSWORD_GM", "correct-password")

    assert authenticate("gm", "wrong-password") is None
