from __future__ import annotations

import os

PLACEHOLDER_FRAGMENTS = ("replace-me", "change-this", "local-dev-password", "local-seed-password")


def is_local_mode() -> bool:
    mode = os.environ.get("BEDO_ENV", os.environ.get("FRAPPE_ENV", "local")).strip().lower()
    return mode in {"local", "dev", "development", "test"}


def require_configured_secret(name: str, value: str | None = None) -> str:
    secret = value if value is not None else os.environ.get(name, "")
    if not secret:
        raise RuntimeError(f"{name} is not configured.")
    lowered = str(secret).lower()
    if not is_local_mode() and any(fragment in lowered for fragment in PLACEHOLDER_FRAGMENTS):
        raise RuntimeError(f"{name} is using a placeholder value outside local development.")
    return str(secret)


def validate_runtime_secrets() -> None:
    required = [
        "BEDO_WEB_SERVICE_SECRET",
        "FRAPPE_ADMIN_PASSWORD",
        "MARIADB_ROOT_PASSWORD",
        "MARIADB_PASSWORD",
    ]
    if os.environ.get("BEDO_WEB_SESSION_SECRET"):
        required.append("BEDO_WEB_SESSION_SECRET")
    for name in required:
        require_configured_secret(name)
