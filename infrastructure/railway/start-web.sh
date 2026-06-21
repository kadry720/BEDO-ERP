#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}"
PORT="${PORT:-8000}"
FRAPPE_WEB_WORKERS="${FRAPPE_WEB_WORKERS:-2}"
FRAPPE_WEB_THREADS="${FRAPPE_WEB_THREADS:-4}"
FRAPPE_GUNICORN_TIMEOUT="${FRAPPE_GUNICORN_TIMEOUT:-120}"
BEDO_FRAPPE_SITE_HEADER="${BEDO_FRAPPE_SITE_HEADER:-${FRAPPE_SITE_NAME}}"

if [ "${BEDO_RUNNING_AS_FRAPPE:-0}" != "1" ]; then
  export BEDO_RUNNING_AS_FRAPPE=1
  exec bash "${ROOT_DIR}/infrastructure/railway/as-frappe.sh" bash "$0" "$@"
fi

bash "${ROOT_DIR}/infrastructure/railway/ensure-bench.sh"
cd "${FRAPPE_BENCH_PATH}"
export FRAPPE_SITE_NAME_HEADER="${FRAPPE_SITE_NAME_HEADER:-${FRAPPE_SITE_NAME}}"
export BEDO_FRAPPE_SITE_HEADER
exec env/bin/gunicorn \
  --pythonpath "${ROOT_DIR}/infrastructure/railway" \
  --bind "0.0.0.0:${PORT}" \
  --workers "${FRAPPE_WEB_WORKERS}" \
  --threads "${FRAPPE_WEB_THREADS}" \
  --timeout "${FRAPPE_GUNICORN_TIMEOUT}" \
  --worker-tmp-dir /dev/shm \
  frappe_wsgi:application
