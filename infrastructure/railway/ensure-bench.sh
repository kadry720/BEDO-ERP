#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}"

if [ "${BEDO_RUNNING_AS_FRAPPE:-0}" != "1" ]; then
  export BEDO_RUNNING_AS_FRAPPE=1
  exec bash "${ROOT_DIR}/infrastructure/railway/as-frappe.sh" bash "$0" "$@"
fi

bash "${ROOT_DIR}/infrastructure/scripts/validate_secrets.sh"
bash "${ROOT_DIR}/infrastructure/scripts/init_project.sh"

if [ ! -d "${FRAPPE_BENCH_PATH}/sites/${FRAPPE_SITE_NAME}" ]; then
  echo "Frappe site ${FRAPPE_SITE_NAME} is missing." >&2
  echo "Run scripts/cloud/railway-init-site.sh as a one-off command before starting runtime services." >&2
  exit 1
fi

cd "${FRAPPE_BENCH_PATH}"
bench --site "${FRAPPE_SITE_NAME}" execute bedo_platform.services.config_validation.validate_runtime_secrets
