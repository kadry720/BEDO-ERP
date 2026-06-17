#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:-bedo.localhost}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${SCRIPT_DIR}/validate_secrets.sh"

cd "${FRAPPE_BENCH_PATH}"
bench --site "${FRAPPE_SITE_NAME}" execute bedo_platform.services.config_validation.validate_runtime_secrets
exec bench start
