#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"
if [ "${BEDO_RUNNING_AS_FRAPPE:-0}" != "1" ]; then
  export BEDO_RUNNING_AS_FRAPPE=1
  exec bash infrastructure/railway/as-frappe.sh bash "$0" "$@"
fi
bash infrastructure/scripts/init_frappe.sh
