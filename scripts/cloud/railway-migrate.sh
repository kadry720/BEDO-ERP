#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"
if [ "${BEDO_RUNNING_AS_FRAPPE:-0}" != "1" ]; then
  export BEDO_RUNNING_AS_FRAPPE=1
  exec bash infrastructure/railway/as-frappe.sh bash "$0" "$@"
fi
bash infrastructure/scripts/run_migrations.sh
cd "${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
bench --site "${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}" execute bedo_platform.services.config_validation.validate_runtime_secrets
