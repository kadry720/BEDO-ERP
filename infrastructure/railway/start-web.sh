#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}"
PORT="${PORT:-8000}"

bash "${ROOT_DIR}/infrastructure/railway/ensure-bench.sh"
cd "${FRAPPE_BENCH_PATH}"
export FRAPPE_SITE_NAME_HEADER="${FRAPPE_SITE_NAME_HEADER:-${FRAPPE_SITE_NAME}}"
exec bench --site "${FRAPPE_SITE_NAME}" serve --port "${PORT}"
