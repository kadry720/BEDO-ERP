#!/usr/bin/env bash
set -euo pipefail

FRAPPE_BENCH_PATH="${FRAPPE_BENCH_PATH:-/workspace/frappe-bench}"

export HOME=/home/frappe
export PATH="/home/frappe/.pyenv/versions/3.14.2/bin:/home/frappe/.local/bin:${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"
export PYTHONPATH="/home/frappe/.bench:/home/frappe/.local/lib/python3.14/site-packages:${PYTHONPATH:-}"

if [ "$(id -u)" = "0" ]; then
  mkdir -p "${FRAPPE_BENCH_PATH}"
  chown -R frappe:frappe "${FRAPPE_BENCH_PATH}"
  exec runuser -u frappe --preserve-environment -- "$@"
fi

exec "$@"
