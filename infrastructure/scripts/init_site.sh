#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:-bedo.localhost}"
FRAPPE_ADMIN_PASSWORD="${FRAPPE_ADMIN_PASSWORD:?FRAPPE_ADMIN_PASSWORD is required}"
MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:?MARIADB_ROOT_PASSWORD is required}"
BEDO_APP_NAME="${BEDO_APP_NAME:-bedo_platform}"

cd "${FRAPPE_BENCH_PATH}"

if [ ! -d "${FRAPPE_BENCH_PATH}/sites/${FRAPPE_SITE_NAME}" ]; then
  bench new-site "${FRAPPE_SITE_NAME}" \
    --mariadb-root-password "${MARIADB_ROOT_PASSWORD}" \
    --admin-password "${FRAPPE_ADMIN_PASSWORD}" \
    --db-host "${MARIADB_HOST:-mariadb}" \
    --db-port "${MARIADB_PORT:-3306}"
fi

if ! bench --site "${FRAPPE_SITE_NAME}" list-apps | grep -qx "${BEDO_APP_NAME}"; then
  bench --site "${FRAPPE_SITE_NAME}" install-app "${BEDO_APP_NAME}"
fi
