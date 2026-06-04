#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
BEDO_APP_NAME="${BEDO_APP_NAME:-bedo_platform}"
BEDO_APP_PATH="${BEDO_APP_PATH:-/workspace/BEDO-ERP/apps/bedo_platform}"

if [ ! -d "${FRAPPE_BENCH_PATH}/apps/frappe" ]; then
  bench init --frappe-branch "${FRAPPE_BRANCH}" "${FRAPPE_BENCH_PATH}"
fi

cd "${FRAPPE_BENCH_PATH}"

bench set-config -g db_host "${MARIADB_HOST:-mariadb}"
bench set-config -g db_port "${MARIADB_PORT:-3306}"
bench set-config -g redis_cache "${REDIS_CACHE_URL:-redis://redis-cache:6379}"
bench set-config -g redis_queue "${REDIS_QUEUE_URL:-redis://redis-queue:6379}"
bench set-config -g redis_socketio "${REDIS_SOCKETIO_URL:-redis://redis-socketio:6379}"

if [ ! -d "${FRAPPE_BENCH_PATH}/apps/${BEDO_APP_NAME}" ]; then
  bench get-app "${BEDO_APP_NAME}" "${BEDO_APP_PATH}"
fi
