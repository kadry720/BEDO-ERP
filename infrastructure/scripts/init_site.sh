#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:-bedo.localhost}"
FRAPPE_ADMIN_PASSWORD="${FRAPPE_ADMIN_PASSWORD:?FRAPPE_ADMIN_PASSWORD is required}"
MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:?MARIADB_ROOT_PASSWORD is required}"

cd "${FRAPPE_BENCH_PATH}"

if [ ! -d "${FRAPPE_BENCH_PATH}/sites/${FRAPPE_SITE_NAME}" ]; then
  bench new-site "${FRAPPE_SITE_NAME}" \
    --mariadb-root-password "${MARIADB_ROOT_PASSWORD}" \
    --admin-password "${FRAPPE_ADMIN_PASSWORD}" \
    --db-host "${MARIADB_HOST:-mariadb}" \
    --db-port "${MARIADB_PORT:-3306}"
fi

if ! bench --site "${FRAPPE_SITE_NAME}" list-apps | grep -qx "bedo_erp"; then
  bench --site "${FRAPPE_SITE_NAME}" install-app bedo_erp
fi

for alias in localhost 127.0.0.1; do
  if [ ! -e "${FRAPPE_BENCH_PATH}/sites/${alias}" ]; then
    ln -s "${FRAPPE_SITE_NAME}" "${FRAPPE_BENCH_PATH}/sites/${alias}"
  fi
done
