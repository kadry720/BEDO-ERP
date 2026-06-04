#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
BEDO_APP_NAME="${BEDO_APP_NAME:-bedo_platform}"
BEDO_APP_PATH="${BEDO_APP_PATH:-/workspace/BEDO-ERP/apps/bedo_platform}"

if [ ! -d "${FRAPPE_BENCH_PATH}/apps/frappe" ]; then
  if [ -d "${FRAPPE_BENCH_PATH}" ] && command -v sudo >/dev/null 2>&1; then
    sudo chown -R "$(id -u):$(id -g)" "${FRAPPE_BENCH_PATH}"
  fi
  bench init --ignore-exist --skip-redis-config-generation --frappe-branch "${FRAPPE_BRANCH}" "${FRAPPE_BENCH_PATH}"
fi

cd "${FRAPPE_BENCH_PATH}"

bench set-mariadb-host "${MARIADB_HOST:-mariadb}"
bench config set-common-config -c db_port "${MARIADB_PORT:-3306}"
bench set-redis-cache-host "${REDIS_CACHE_URL:-redis://redis-cache:6379}"
bench set-redis-queue-host "${REDIS_QUEUE_URL:-redis://redis-queue:6379}"
bench set-redis-socketio-host "${REDIS_SOCKETIO_URL:-redis://redis-socketio:6379}"

if [ ! -d "${FRAPPE_BENCH_PATH}/apps/${BEDO_APP_NAME}" ]; then
  ln -s "${BEDO_APP_PATH}" "${FRAPPE_BENCH_PATH}/apps/${BEDO_APP_NAME}"
fi

bench pip install "ldap3>=2.9.1,<3.0.0"
bench pip install --no-deps -e "${FRAPPE_BENCH_PATH}/apps/${BEDO_APP_NAME}"

if ! grep -qx "${BEDO_APP_NAME}" "${FRAPPE_BENCH_PATH}/sites/apps.txt"; then
  if [ -s "${FRAPPE_BENCH_PATH}/sites/apps.txt" ] && [ "$(tail -c 1 "${FRAPPE_BENCH_PATH}/sites/apps.txt")" != "" ]; then
    printf '\n' >> "${FRAPPE_BENCH_PATH}/sites/apps.txt"
  fi
  printf '%s\n' "${BEDO_APP_NAME}" >> "${FRAPPE_BENCH_PATH}/sites/apps.txt"
fi
