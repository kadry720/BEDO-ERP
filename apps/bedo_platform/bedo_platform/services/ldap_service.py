from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LDAPConfig:
    uri: str
    base_dn: str
    bind_dn: str
    bind_password: str
    user_search_filter: str
    use_tls: bool = True
    cert_required: bool = True
    timeout: int = 5


@dataclass(frozen=True)
class LDAPUser:
    username: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone_number: str = ""


class LDAPAdapter(Protocol):
    def authenticate(self, username: str, password: str) -> LDAPUser | None:
        ...

    def provision_user(self, user: LDAPUser, password: str) -> bool:
        ...

    def change_password(self, username: str, password: str) -> bool:
        ...


def _get_config_value(key: str, default: str = "") -> str:
    try:
        import frappe

        value = frappe.conf.get(key) or frappe.conf.get(key.lower())
        if value is not None:
            return str(value)
    except Exception:
        pass
    return os.environ.get(key, default)


def get_ldap_config() -> LDAPConfig:
    uri = _get_config_value("LDAP_URI") or _get_config_value("LDAP_SERVER_URL")
    return LDAPConfig(
        uri=uri,
        base_dn=_get_config_value("LDAP_BASE_DN"),
        bind_dn=_get_config_value("LDAP_BIND_DN"),
        bind_password=_get_config_value("LDAP_BIND_PASSWORD"),
        user_search_filter=_get_config_value("LDAP_USER_SEARCH_FILTER", "(uid={username})"),
        use_tls=_get_config_value("LDAP_USE_TLS", "true").lower() in {"1", "true", "yes"},
        cert_required=_get_config_value("LDAP_CERT_REQUIRED", "true").lower() in {"1", "true", "yes"},
        timeout=int(_get_config_value("LDAP_TIMEOUT", "5")),
    )


class MockLDAPAdapter:
    def _cached_password(self, username: str) -> str:
        try:
            import frappe

            return str(frappe.cache().get_value(f"bedo_mock_ldap_password:{username}") or "")
        except Exception:
            return ""

    def authenticate(self, username: str, password: str) -> LDAPUser | None:
        if not username or not password:
            return None
        env_key = f"BEDO_MOCK_LDAP_PASSWORD_{username.upper().replace('.', '_').replace('-', '_')}"
        expected = os.environ.get(env_key)
        expected = self._cached_password(username) or expected
        if expected and expected == password:
            return LDAPUser(username=username, email=f"{username}@bedo.local")
        return None

    def provision_user(self, user: LDAPUser, password: str) -> bool:
        self.change_password(user.username, password)
        return bool(user.username and password)

    def change_password(self, username: str, password: str) -> bool:
        if not username or not password:
            return False
        try:
            import frappe

            frappe.cache().set_value(f"bedo_mock_ldap_password:{username}", password, expires_in_sec=60 * 60 * 24 * 365)
        except Exception:
            return False
        return True


class LDAP3Adapter:
    def __init__(self, config: LDAPConfig):
        self.config = config

    def authenticate(self, username: str, password: str) -> LDAPUser | None:
        if not username or not password:
            return None

        from ldap3 import ALL, Connection, Server, Tls

        tls = None
        if self.config.use_tls:
            tls = Tls(validate=2 if self.config.cert_required else 0)

        server = Server(
            self.config.uri,
            get_info=ALL,
            connect_timeout=self.config.timeout,
            tls=tls,
        )
        service_connection = Connection(
            server,
            user=self.config.bind_dn,
            password=self.config.bind_password,
            auto_bind=True,
            receive_timeout=self.config.timeout,
        )
        search_filter = self.config.user_search_filter.format(username=username)
        service_connection.search(
            self.config.base_dn,
            search_filter,
            attributes=["uid", "givenName", "sn", "mail", "telephoneNumber"],
        )
        if not service_connection.entries:
            return None

        entry = service_connection.entries[0]
        user_dn = entry.entry_dn
        if not Connection(server, user=user_dn, password=password, auto_bind=True):
            return None

        return LDAPUser(
            username=username,
            first_name=str(getattr(entry, "givenName", "") or ""),
            last_name=str(getattr(entry, "sn", "") or ""),
            email=str(getattr(entry, "mail", "") or ""),
            phone_number=str(getattr(entry, "telephoneNumber", "") or ""),
        )

    def provision_user(self, user: LDAPUser, password: str) -> bool:
        raise NotImplementedError("Production LDAP provisioning must be wired to the organization's LDAP adapter.")

    def change_password(self, username: str, password: str) -> bool:
        raise NotImplementedError("Production LDAP password changes must be wired to the organization's LDAP adapter.")


def get_adapter() -> LDAPAdapter:
    adapter_name = _get_config_value("BEDO_LDAP_ADAPTER", "").lower()
    config = get_ldap_config()
    if adapter_name == "mock" or config.uri.startswith("mock://"):
        return MockLDAPAdapter()
    if not config.uri:
        raise RuntimeError("LDAP_URI is required for LDAP-only authentication.")
    return LDAP3Adapter(config)


def authenticate(username: str, password: str) -> LDAPUser | None:
    return get_adapter().authenticate(username, password)


def provision_user(user: LDAPUser, password: str) -> bool:
    return get_adapter().provision_user(user, password)


def change_password(username: str, password: str) -> bool:
    return get_adapter().change_password(username, password)
