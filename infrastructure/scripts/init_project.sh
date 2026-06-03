#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
BEDO_APP_PATH="${BEDO_APP_PATH:-/workspace/BEDO-ERP/apps/bedo_erp}"
BENCH_INIT_ARGS=()

if [ -d "${FRAPPE_BENCH_PATH}" ] && [ ! -d "${FRAPPE_BENCH_PATH}/apps/frappe" ]; then
  if [ -z "$(find "${FRAPPE_BENCH_PATH}" -mindepth 1 -maxdepth 1)" ]; then
    BENCH_INIT_ARGS+=(--ignore-exist)
  else
    echo "Bench path exists but is not a valid bench: ${FRAPPE_BENCH_PATH}" >&2
    exit 1
  fi
fi

if [ ! -d "${FRAPPE_BENCH_PATH}/apps/frappe" ]; then
  bench init "${BENCH_INIT_ARGS[@]}" --skip-redis-config-generation --frappe-branch "${FRAPPE_BRANCH}" "${FRAPPE_BENCH_PATH}"
fi

cd "${FRAPPE_BENCH_PATH}"

bench set-mariadb-host "${MARIADB_HOST:-mariadb}"
bench config set-common-config -c db_port "${MARIADB_PORT:-3306}"
bench config set-common-config -c redis_cache "\"${REDIS_CACHE_URL:-redis://redis-cache:6379}\""
bench config set-common-config -c redis_queue "\"${REDIS_QUEUE_URL:-redis://redis-queue:6379}\""
bench config set-common-config -c redis_socketio "\"${REDIS_SOCKETIO_URL:-redis://redis-socketio:6379}\""

if [ ! -e "${FRAPPE_BENCH_PATH}/apps/bedo_erp" ]; then
  ln -s "${BEDO_APP_PATH}" "${FRAPPE_BENCH_PATH}/apps/bedo_erp"
fi

"${FRAPPE_BENCH_PATH}/env/bin/python" -m pip install --no-deps --editable "${FRAPPE_BENCH_PATH}/apps/bedo_erp"

touch "${FRAPPE_BENCH_PATH}/sites/apps.txt"
"${FRAPPE_BENCH_PATH}/env/bin/python" - "${FRAPPE_BENCH_PATH}/sites/apps.txt" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
raw_apps = path.read_text().splitlines() if path.exists() else []
apps = []
for app in raw_apps:
    if app == "frappebedo_erp":
        apps.extend(["frappe", "bedo_erp"])
    elif app:
        apps.append(app)
for app in ("frappe", "bedo_erp"):
    if app not in apps:
        apps.append(app)
path.write_text("\n".join(dict.fromkeys(apps)) + "\n")
PY
