#!/usr/bin/env python3
from __future__ import annotations

import argparse
import secrets
import socket
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"


GENERATED_KEYS = {
    "MARIADB_ROOT_PASSWORD",
    "MARIADB_PASSWORD",
    "FRAPPE_ADMIN_PASSWORD",
    "BEDO_WEB_SERVICE_SECRET",
    "BEDO_WEB_SESSION_SECRET",
    "BEDO_SEED_DEFAULT_PASSWORD",
    "BEDO_SEED_GM_PASSWORD",
}


def secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return ""


def generated_values() -> dict[str, str]:
    seed_password = secret(18)
    ip_address = lan_ip()
    public_url = "http://localhost:3000"
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    if ip_address:
        origins.append(f"http://{ip_address}:3000")
    return {
        "MARIADB_ROOT_PASSWORD": secret(),
        "MARIADB_PASSWORD": secret(),
        "FRAPPE_ADMIN_PASSWORD": secret(24),
        "BEDO_WEB_SERVICE_SECRET": secret(),
        "BEDO_WEB_SESSION_SECRET": secret(),
        "BEDO_SEED_DEFAULT_PASSWORD": seed_password,
        "BEDO_SEED_GM_PASSWORD": seed_password,
        "BEDO_FORCE_SEED_PASSWORD_RESET": "0",
        "BEDO_WEB_PUBLIC_URL": public_url,
        "BEDO_WEB_ALLOWED_DEV_ORIGINS": ",".join(origins),
    }


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def render_env() -> str:
    replacements = generated_values()
    lines = []
    for line in EXAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            lines.append(line)
            continue
        key, _value = line.split("=", 1)
        key = key.strip()
        lines.append(f"{key}={replacements.get(key, _value)}")
    return "\n".join(lines).rstrip() + "\n"


def append_missing_values() -> int:
    existing = parse_env(ENV_PATH)
    replacements = generated_values()
    missing_lines = []
    for line in EXAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in existing:
            missing_lines.append(f"{key}={replacements.get(key, value)}")
    if not missing_lines:
        return 0
    with ENV_PATH.open("a", encoding="utf-8") as handle:
        handle.write("\n# Added by scripts/generate_env.py for new BEDO settings\n")
        handle.write("\n".join(missing_lines))
        handle.write("\n")
    return len(missing_lines)


def print_credentials() -> None:
    values = parse_env(ENV_PATH)
    seed_password = values.get("BEDO_SEED_GM_PASSWORD") or values.get("BEDO_SEED_DEFAULT_PASSWORD") or ""
    print("Local BEDO bootstrap account")
    print("Username: gm")
    print(f"Password: {seed_password or '(not configured)'}")
    print(f"URL: {values.get('BEDO_WEB_PUBLIC_URL', 'http://localhost:3000')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate BEDO local environment secrets.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing .env file.")
    parser.add_argument("--print-credentials", action="store_true", help="Print local bootstrap credentials from .env.")
    args = parser.parse_args()

    if args.print_credentials:
        print_credentials()
        return 0

    if ENV_PATH.exists() and not args.force:
        added = append_missing_values()
        if added:
            print(f"{ENV_PATH} already exists; appended {added} missing setting(s).")
        else:
            print(f"{ENV_PATH} already exists; leaving it unchanged.")
        return 0
    ENV_PATH.write_text(render_env(), encoding="utf-8")
    print(f"Generated {ENV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
