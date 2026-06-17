#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse


PLACEHOLDER_FRAGMENTS = ("replace-me", "change-this", "your-", "example.com", "<", ">")

REQUIRED = {
    "vercel": [
        "BEDO_ENV",
        "FRAPPE_INTERNAL_URL",
        "BEDO_WEB_PUBLIC_URL",
        "BEDO_WEB_SERVICE_SECRET",
        "BEDO_WEB_SESSION_SECRET",
        "BEDO_SESSION_REDIS_URL",
        "NEXT_PUBLIC_BEDO_APP_NAME",
    ],
    "railway": [
        "BEDO_ENV",
        "FRAPPE_SITE_NAME",
        "FRAPPE_ADMIN_PASSWORD",
        "MARIADB_HOST",
        "MARIADB_PORT",
        "MARIADB_ROOT_PASSWORD",
        "MARIADB_PASSWORD",
        "REDIS_CACHE_URL",
        "REDIS_QUEUE_URL",
        "REDIS_SOCKETIO_URL",
        "BEDO_WEB_PUBLIC_URL",
        "BEDO_WEB_SERVICE_SECRET",
    ],
}

SECRET_NAMES = {
    "BEDO_WEB_SERVICE_SECRET",
    "BEDO_WEB_SESSION_SECRET",
    "FRAPPE_ADMIN_PASSWORD",
    "MARIADB_ROOT_PASSWORD",
    "MARIADB_PASSWORD",
    "BEDO_SEED_DEFAULT_PASSWORD",
}


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in PLACEHOLDER_FRAGMENTS)


def is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def is_redis_url(value: str, *, require_tls: bool) -> bool:
    parsed = urlparse(value)
    allowed = {"rediss"} if require_tls else {"redis", "rediss"}
    return parsed.scheme in allowed and bool(parsed.netloc)


def validate_values(target: str, values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    production = values.get("BEDO_ENV", "").lower() == "production"
    for name in REQUIRED[target]:
        if not values.get(name):
            errors.append(f"{name} is required for {target}.")

    if production:
        for name in SECRET_NAMES:
            value = values.get(name, "")
            if value and is_placeholder(value):
                errors.append(f"{name} uses a placeholder value.")

    if target == "vercel":
        for name in ("FRAPPE_INTERNAL_URL", "BEDO_WEB_PUBLIC_URL"):
            value = values.get(name, "")
            if value and production and not is_https_url(value):
                errors.append(f"{name} must be an https URL in production.")
        redis_url = values.get("BEDO_SESSION_REDIS_URL", "")
        if redis_url and production and not is_redis_url(redis_url, require_tls=True):
            errors.append("BEDO_SESSION_REDIS_URL must be a rediss:// URL reachable from Vercel in production.")

    if target == "railway":
        public_url = values.get("BEDO_WEB_PUBLIC_URL", "")
        if public_url and production and not is_https_url(public_url):
            errors.append("BEDO_WEB_PUBLIC_URL must be an https URL in production.")
        for name in ("REDIS_CACHE_URL", "REDIS_QUEUE_URL", "REDIS_SOCKETIO_URL"):
            value = values.get(name, "")
            if value and not is_redis_url(value, require_tls=False):
                errors.append(f"{name} must be a redis:// or rediss:// URL.")
        port = values.get("MARIADB_PORT", "")
        if port and not port.isdigit():
            errors.append("MARIADB_PORT must be numeric.")

    return errors


def validate_shared_values(vercel: dict[str, str], railway: dict[str, str]) -> list[str]:
    if vercel.get("BEDO_WEB_SERVICE_SECRET") != railway.get("BEDO_WEB_SERVICE_SECRET"):
        return ["BEDO_WEB_SERVICE_SECRET must match between Vercel and Railway."]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BEDO cloud env files before setting platform secrets.")
    parser.add_argument("--vercel", type=Path, help="Path to Vercel env file.")
    parser.add_argument("--railway", type=Path, help="Path to Railway env file.")
    args = parser.parse_args()

    if not args.vercel and not args.railway:
        parser.error("provide --vercel, --railway, or both")

    errors: list[str] = []
    vercel = parse_env(args.vercel) if args.vercel else None
    railway = parse_env(args.railway) if args.railway else None
    if vercel is not None:
        errors.extend(validate_values("vercel", vercel))
    if railway is not None:
        errors.extend(validate_values("railway", railway))
    if vercel is not None and railway is not None:
        errors.extend(validate_shared_values(vercel, railway))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Cloud env validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
