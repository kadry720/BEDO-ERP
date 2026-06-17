from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(path: str):
    spec = importlib.util.spec_from_file_location(path.replace("/", "_").replace(".", "_"), ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_cloud_env_rejects_placeholder_secret():
    validator = load_script("scripts/cloud/validate-cloud-env.py")

    errors = validator.validate_values(
        "vercel",
        {
            "BEDO_ENV": "production",
            "FRAPPE_INTERNAL_URL": "https://bedo-backend.up.railway.app",
            "BEDO_WEB_PUBLIC_URL": "https://bedo.vercel.app",
            "BEDO_WEB_SERVICE_SECRET": "replace-me",
            "BEDO_WEB_SESSION_SECRET": "strong-session-secret",
            "BEDO_SESSION_REDIS_URL": "rediss://default:secret@example.upstash.io:6379",
            "NEXT_PUBLIC_BEDO_APP_NAME": "BEDO",
        },
    )

    assert any("BEDO_WEB_SERVICE_SECRET uses a placeholder" in error for error in errors)


def test_validate_cloud_env_checks_shared_secret_match():
    validator = load_script("scripts/cloud/validate-cloud-env.py")

    errors = validator.validate_shared_values(
        {"BEDO_WEB_SERVICE_SECRET": "same-secret"},
        {"BEDO_WEB_SERVICE_SECRET": "other-secret"},
    )

    assert errors == ["BEDO_WEB_SERVICE_SECRET must match between Vercel and Railway."]


def test_generate_cloud_env_outputs_separate_vercel_and_railway_files(tmp_path):
    generator = load_script("scripts/cloud/generate-cloud-env.py")

    files = generator.generate_files(
        tmp_path,
        vercel_url="https://bedo.vercel.app",
        railway_url="https://bedo-backend.up.railway.app",
        session_redis_url="rediss://default:secret@example.upstash.io:6379",
        force=False,
    )

    vercel = files["vercel"].read_text(encoding="utf-8")
    railway = files["railway"].read_text(encoding="utf-8")
    assert "FRAPPE_INTERNAL_URL=https://bedo-backend.up.railway.app" in vercel
    assert "BEDO_WEB_PUBLIC_URL=https://bedo.vercel.app" in railway
    assert "MARIADB_HOST=" in railway
    assert "BEDO_WEB_SESSION_SECRET=" in vercel
