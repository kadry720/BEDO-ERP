from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from bedo_platform.services import service_auth


class FakePermissionError(Exception):
    pass


class FakeCache:
    def __init__(self):
        self.values = {}

    def get_value(self, key):
        return self.values.get(key)

    def set_value(self, key, value, expires_in_sec=None):
        self.values[key] = value


class FakeDb:
    def get_value(self, *args, **kwargs):
        return 1


class FakeRequest:
    method = "POST"
    path = "/api/method/bedo_platform.api.web.me"

    def __init__(self, headers, body=b"{}"):
        self.headers = headers
        self._body = body

    def get_data(self):
        return self._body


class FakeFrappe:
    PermissionError = FakePermissionError
    conf = {"BEDO_WEB_SERVICE_SECRET": "unit-test-service-secret"}
    db = FakeDb()

    def __init__(self, cache):
        self._cache = cache
        self.local = SimpleNamespace(request=None)

    def cache(self):
        return self._cache

    def throw(self, message, exc):
        raise exc(message)


def _signed_headers(secret: str, *, signature: str | None = None, nonce: str = "nonce-1"):
    timestamp = str(int(time.time()))
    expected = service_auth._expected_signature(
        secret=secret,
        service="bedo-web",
        user="gm",
        timestamp=timestamp,
        nonce=nonce,
        method="POST",
        path=FakeRequest.path,
        body=b"{}",
    )
    return {
        service_auth.SERVICE_HEADER: "bedo-web",
        service_auth.USER_HEADER: "gm",
        service_auth.TIMESTAMP_HEADER: timestamp,
        service_auth.NONCE_HEADER: nonce,
        service_auth.SIGNATURE_HEADER: signature or expected,
    }


def test_invalid_signature_does_not_consume_nonce(monkeypatch):
    monkeypatch.setenv("BEDO_ENV", "local")
    cache = FakeCache()
    fake_frappe = FakeFrappe(cache)
    fake_frappe.local.request = FakeRequest(_signed_headers("unit-test-service-secret", signature="bad"))
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    with pytest.raises(FakePermissionError):
        service_auth.validate_service_request()

    assert cache.values == {}


def test_valid_signature_consumes_nonce_and_replay_fails(monkeypatch):
    monkeypatch.setenv("BEDO_ENV", "local")
    cache = FakeCache()
    fake_frappe = FakeFrappe(cache)
    headers = _signed_headers("unit-test-service-secret")
    fake_frappe.local.request = FakeRequest(headers)
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert service_auth.validate_service_request() == "gm"
    assert cache.values

    fake_frappe.local = SimpleNamespace(request=FakeRequest(headers))
    with pytest.raises(FakePermissionError):
        service_auth.validate_service_request()


def test_web_api_functions_use_service_api_decorator():
    source_path = Path(__file__).parents[1] / "api" / "web.py"
    lines = source_path.read_text(encoding="utf-8").splitlines()
    skipped = {"service_api", "_payload"}
    missing = []
    for index, line in enumerate(lines):
        if not line.startswith("def "):
            continue
        name = line.split("def ", 1)[1].split("(", 1)[0]
        if name.startswith("_") or name in skipped:
            continue
        previous = next((candidate.strip() for candidate in reversed(lines[:index]) if candidate.strip()), "")
        if previous != "@service_api":
            missing.append(name)

    assert missing == []
