#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_SITE_NAME="${FRAPPE_SITE_NAME:-bedo.localhost}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${SCRIPT_DIR}/validate_secrets.sh"
BEDO_APP_NAME="${BEDO_APP_NAME:-bedo_platform}"
BEDO_APP_PATH="${BEDO_APP_PATH:-/workspace/BEDO-ERP/apps/bedo_platform}"
MARIADB_HOST="${MARIADB_HOST:-mariadb}"
MARIADB_PORT="${MARIADB_PORT:-3306}"

wait_for_mariadb() {
  python - <<'PY'
import os
import socket
import time

host = os.environ.get("MARIADB_HOST", "mariadb")
port = int(os.environ.get("MARIADB_PORT", "3306"))
deadline = time.time() + 120

while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        if time.time() >= deadline:
            raise SystemExit(f"MariaDB at {host}:{port} did not become ready in time")
        time.sleep(2)
PY
}

wait_for_mariadb

bash /workspace/BEDO-ERP/infrastructure/scripts/init_project.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/init_site.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/run_migrations.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/seed_phase_1_data.sh

cd "${FRAPPE_BENCH_PATH}"
exec bench start
