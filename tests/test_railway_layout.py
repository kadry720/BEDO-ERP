from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_railway_image_prebuilds_frappe_bench_outside_volume():
    dockerfile = read("infrastructure/railway/frappe.Dockerfile")

    assert "bench init" in dockerfile
    assert "/workspace/frappe-bench" in dockerfile


def test_railway_config_does_not_override_dashboard_runtime_commands():
    config = read("railway.toml")

    assert "dockerfilePath" in config
    assert "startCommand" not in config
    assert "healthcheckPath" not in config


def test_railway_root_helper_only_prepares_sites_volume():
    helper = read("infrastructure/railway/as-frappe.sh")

    assert 'FRAPPE_SITES_PATH="${FRAPPE_SITES_PATH:-${FRAPPE_BENCH_PATH}/sites}"' in helper
    assert 'chown -R frappe:frappe "${FRAPPE_SITES_PATH}"' in helper
    assert 'chown -R frappe:frappe "${FRAPPE_BENCH_PATH}"' not in helper


def test_docs_mount_volume_at_frappe_sites_path():
    docs = "\n".join(
        [
            read("README.md"),
            read("docs/deployment/vercel-railway-neon.md"),
            read("docs/deployment/manual-interventions.md"),
            read("docs/deployment/architecture-decisions.md"),
        ]
    )

    assert "Mount at `/workspace/frappe-bench/sites`" in docs
    assert "Mount at `/workspace/frappe-bench`" not in docs
