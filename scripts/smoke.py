#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SMOKE_USERNAMES = (
    "gm",
    "gm@bedo.local",
    "systemadmin",
    "systemadmin@bedo.local",
    "useradmin",
    "useradmin@bedo.local",
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise SystemExit(".env is missing. Run ./scripts/bedo up first.")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def request_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    payload: dict[str, str] | None = None,
    origin: str = "",
) -> tuple[int, dict]:
    data = None
    headers = {}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Origin"] = origin
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body or "{}")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        return error.code, json.loads(body or "{}")


def smoke_credentials(values: dict[str, str]) -> list[tuple[str, str]]:
    password = values.get("BEDO_SEED_GM_PASSWORD") or values.get("BEDO_SEED_DEFAULT_PASSWORD") or ""
    if not password:
        raise SystemExit("No local bootstrap password is configured in .env.")

    usernames = []
    configured = values.get("BEDO_SMOKE_USERNAME", "").strip()
    if configured:
        usernames.append(configured)
    usernames.extend(DEFAULT_SMOKE_USERNAMES)

    seen = set()
    credentials = []
    for username in usernames:
        if username and username not in seen:
            credentials.append((username, password))
            seen.add(username)
    return credentials


def login_with_candidates(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    credentials: list[tuple[str, str]],
) -> tuple[str, dict]:
    attempts = []
    for username, password in credentials:
        status, result = request_json(opener, f"{base_url}/api/auth/login", {"username": username, "password": password}, base_url)
        if status == 200 and result.get("route"):
            return username, result
        attempts.append(f"{username}: HTTP {status}")
    raise SystemExit(f"Login failed for configured seed users ({'; '.join(attempts)}).")


def logout(cookie_jar: CookieJar, base_url: str) -> None:
    no_redirect = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar), NoRedirect())
    logout_request = urllib.request.Request(f"{base_url}/api/auth/logout", data=b"", headers={"Origin": base_url}, method="POST")
    try:
        no_redirect.open(logout_request, timeout=20).read()
    except urllib.error.HTTPError as error:
        if error.code not in {303, 307, 308}:
            raise SystemExit(f"Logout failed: HTTP {error.code}")


def main() -> int:
    values = read_env()
    base_url = values.get("BEDO_WEB_PUBLIC_URL", "http://localhost:3000").rstrip("/")
    credentials = smoke_credentials(values)

    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    status, health = request_json(opener, f"{base_url}/api/health")
    if status != 200 or health.get("status") != "ok":
        raise SystemExit(f"Health check failed: HTTP {status} {health}")

    username, first_login = login_with_candidates(opener, base_url, credentials)

    logout(cookie_jar, base_url)

    status, second_login = request_json(
        opener,
        f"{base_url}/api/auth/login",
        {"username": username, "password": dict(credentials)[username]},
        base_url,
    )
    if status != 200 or not second_login.get("route"):
        raise SystemExit(f"Second login failed: HTTP {status} {second_login}")
    logout(cookie_jar, base_url)

    print(f"Smoke checks passed: health, login ({username}), logout, login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
