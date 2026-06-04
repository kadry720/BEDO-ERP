#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:-bedo.localhost}"

cd "${FRAPPE_BENCH_PATH}"
bench --site "${FRAPPE_SITE_NAME}" execute bedo_platform.setup.seed_all.execute
bench --site "${FRAPPE_SITE_NAME}" execute bedo_platform.setup.seed_initial_users.execute --kwargs "{'strict': true}"
