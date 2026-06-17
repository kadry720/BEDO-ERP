#!/usr/bin/env python3
from __future__ import annotations

import argparse
import secrets
from pathlib import Path


VERCEL_FILE = ".env.vercel.local.generated"
RAILWAY_FILE = ".env.railway.local.generated"


def secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def render_env(values: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in values.items()).rstrip() + "\n"


def generated_values(
    *,
    vercel_url: str,
    railway_url: str,
    session_redis_url: str,
) -> tuple[dict[str, str], dict[str, str]]:
    service_secret = secret()
    bootstrap_password = secret(18)
    vercel = {
        "BEDO_ENV": "production",
        "FRAPPE_INTERNAL_URL": railway_url,
        "BEDO_WEB_PUBLIC_URL": vercel_url,
        "BEDO_WEB_SERVICE_SECRET": service_secret,
        "BEDO_WEB_SESSION_SECRET": secret(),
        "BEDO_SESSION_REDIS_URL": session_redis_url,
        "NEXT_PUBLIC_BEDO_APP_NAME": "BEDO",
    }
    railway = {
        "BEDO_ENV": "production",
        "FRAPPE_BRANCH": "version-15",
        "FRAPPE_BENCH_PATH": "/workspace/frappe-bench",
        "BEDO_APP_NAME": "bedo_platform",
        "BEDO_APP_PATH": "/workspace/BEDO-ERP/apps/bedo_platform",
        "FRAPPE_SITE_NAME": "bedo.example.com",
        "FRAPPE_ADMIN_PASSWORD": secret(24),
        "MARIADB_HOST": "",
        "MARIADB_PORT": "3306",
        "MARIADB_ROOT_PASSWORD": "",
        "MARIADB_PASSWORD": "",
        "REDIS_CACHE_URL": "",
        "REDIS_QUEUE_URL": "",
        "REDIS_SOCKETIO_URL": "",
        "BEDO_WEB_PUBLIC_URL": vercel_url,
        "BEDO_WEB_SERVICE_SECRET": service_secret,
        "BEDO_FORCE_SEED_PASSWORD_RESET": "0",
        "BEDO_SEED_DEFAULT_PASSWORD": bootstrap_password,
        "BEDO_SRS_DEADLINE_MODE": "working_days",
    }
    return vercel, railway


def write_env(path: Path, values: dict[str, str], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists. Use --force to overwrite it.")
    path.write_text(render_env(values), encoding="utf-8")


def generate_files(
    output_dir: Path,
    *,
    vercel_url: str,
    railway_url: str,
    session_redis_url: str,
    force: bool,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    vercel, railway = generated_values(
        vercel_url=vercel_url,
        railway_url=railway_url,
        session_redis_url=session_redis_url,
    )
    files = {
        "vercel": output_dir / VERCEL_FILE,
        "railway": output_dir / RAILWAY_FILE,
    }
    write_env(files["vercel"], vercel, force=force)
    write_env(files["railway"], railway, force=force)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ignored BEDO cloud env files for Vercel and Railway.")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Directory for generated env files.")
    parser.add_argument("--vercel-url", default="https://your-vercel-domain.vercel.app", help="Public Next.js URL.")
    parser.add_argument("--railway-url", default="https://your-railway-frappe-domain.up.railway.app", help="Public Frappe URL.")
    parser.add_argument(
        "--session-redis-url",
        default="rediss://default:password@your-session-redis.example.com:6379",
        help="TLS Redis URL reachable from Vercel for the Next session registry.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated files.")
    args = parser.parse_args()

    files = generate_files(
        args.output_dir,
        vercel_url=args.vercel_url.rstrip("/"),
        railway_url=args.railway_url.rstrip("/"),
        session_redis_url=args.session_redis_url,
        force=args.force,
    )
    print(f"Wrote {files['vercel']}")
    print(f"Wrote {files['railway']}")
    print("Generated files are ignored by git. Copy values into Vercel and Railway secret stores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
