#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}"
BEDO_APP_NAME="${BEDO_APP_NAME:-bedo_platform}"

cd "${ROOT_DIR}"
bash infrastructure/scripts/validate_secrets.sh

cd "${FRAPPE_BENCH_PATH}"
if [ ! -d "sites/${FRAPPE_SITE_NAME}" ]; then
  echo "Frappe site ${FRAPPE_SITE_NAME} is missing." >&2
  exit 1
fi

bench --site "${FRAPPE_SITE_NAME}" mariadb -e "select 1;"
bench --site "${FRAPPE_SITE_NAME}" list-apps | grep -qx "${BEDO_APP_NAME}"
bench --site "${FRAPPE_SITE_NAME}" execute bedo_platform.services.config_validation.validate_runtime_secrets

echo "Railway doctor passed: site, MariaDB, installed app, and runtime secrets are valid."
