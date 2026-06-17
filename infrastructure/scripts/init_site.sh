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

python - <<'PY'
import json
import os
import subprocess
from pathlib import Path

bench_path = Path(os.environ.get("FRAPPE_BENCH_PATH", "/workspace/frappe-bench"))
site_name = os.environ.get("FRAPPE_SITE_NAME", "bedo.localhost")
site_config = bench_path / "sites" / site_name / "site_config.json"
if not site_config.exists():
    raise SystemExit(f"{site_config} is missing")

config = json.loads(site_config.read_text(encoding="utf-8"))
db_name = str(config.get("db_name") or "").strip()
db_password = str(config.get("db_password") or "")
db_host = os.environ.get("MARIADB_HOST", "mariadb")
db_port = os.environ.get("MARIADB_PORT", "3306")
root_password = os.environ.get("MARIADB_ROOT_PASSWORD", "")
if not db_name or not db_password or not root_password:
    raise SystemExit("Site database credentials are incomplete.")

def sql_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"

def sql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"

db_identifier = sql_identifier(db_name)
password_literal = sql_string(db_password)
statements = [
    f"CREATE USER IF NOT EXISTS {db_identifier}@'%' IDENTIFIED BY {password_literal}",
    f"ALTER USER {db_identifier}@'%' IDENTIFIED BY {password_literal}",
    f"GRANT ALL PRIVILEGES ON {db_identifier}.* TO {db_identifier}@'%'",
    "FLUSH PRIVILEGES",
]
sql = ";\n".join(statements) + ";\n"
subprocess.run(
    ["mariadb", "-h", db_host, "-P", str(db_port), "-uroot", f"-p{root_password}"],
    input=sql,
    text=True,
    check=True,
)
PY

if ! bench --site "${FRAPPE_SITE_NAME}" list-apps | grep -qx "${BEDO_APP_NAME}"; then
  bench --site "${FRAPPE_SITE_NAME}" install-app "${BEDO_APP_NAME}"
fi
