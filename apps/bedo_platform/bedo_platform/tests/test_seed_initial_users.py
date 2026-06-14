from bedo_platform.constants import INITIAL_USERS, SEED_DEFAULT_PASSWORD_ENV
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
