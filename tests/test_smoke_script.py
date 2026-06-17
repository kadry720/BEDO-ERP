from __future__ import annotations

import importlib.util
from pathlib import Path


def load_smoke_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "smoke.py"
    spec = importlib.util.spec_from_file_location("bedo_smoke", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_login_with_candidates_falls_back_after_failed_seed_user(monkeypatch):
    smoke = load_smoke_module()
    calls: list[str] = []

    def fake_request_json(_opener, _url, payload=None, _origin=""):
        username = payload["username"]
        calls.append(username)
        if username == "systemadmin":
            return 200, {"route": "/admin"}
        return 401, {"error": "Invalid username or password."}

    monkeypatch.setattr(smoke, "request_json", fake_request_json)

    username, result = smoke.login_with_candidates(
        object(),
        "http://localhost:3000",
        [("gm", "123456"), ("systemadmin", "123456")],
    )

    assert username == "systemadmin"
    assert result == {"route": "/admin"}
    assert calls == ["gm", "systemadmin"]


def test_smoke_credentials_include_configured_user_before_seed_fallbacks():
    smoke = load_smoke_module()

    credentials = smoke.smoke_credentials(
        {
            "BEDO_SMOKE_USERNAME": "custom",
            "BEDO_SEED_DEFAULT_PASSWORD": "123456",
            "BEDO_SEED_GM_PASSWORD": "123456",
        }
    )

    assert credentials[:3] == [
        ("custom", "123456"),
        ("gm", "123456"),
        ("gm@bedo.local", "123456"),
    ]
    assert ("systemadmin", "123456") in credentials
