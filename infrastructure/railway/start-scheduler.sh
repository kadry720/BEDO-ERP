#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}"

if [ "${BEDO_RUNNING_AS_FRAPPE:-0}" != "1" ]; then
  export BEDO_RUNNING_AS_FRAPPE=1
  exec bash "${ROOT_DIR}/infrastructure/railway/as-frappe.sh" bash "$0" "$@"
fi

bash "${ROOT_DIR}/infrastructure/railway/ensure-bench.sh"
cd "${FRAPPE_BENCH_PATH}"
exec bench --site "${FRAPPE_SITE_NAME}" schedule
