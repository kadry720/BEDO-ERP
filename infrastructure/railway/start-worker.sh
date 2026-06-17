#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}"
FRAPPE_WORKER_QUEUES="${FRAPPE_WORKER_QUEUES:-default,short,long}"

bash "${ROOT_DIR}/infrastructure/railway/ensure-bench.sh"
cd "${FRAPPE_BENCH_PATH}"
exec bench --site "${FRAPPE_SITE_NAME}" worker --queue "${FRAPPE_WORKER_QUEUES}"
