#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"
if [ "${BEDO_RUNNING_AS_FRAPPE:-0}" != "1" ]; then
  export BEDO_RUNNING_AS_FRAPPE=1
  exec bash infrastructure/railway/as-frappe.sh bash "$0" "$@"
fi
if [ "${BEDO_FORCE_SEED_PASSWORD_RESET:-0}" = "1" ]; then
  echo "BEDO_FORCE_SEED_PASSWORD_RESET=1 is set; seed passwords will be reset intentionally." >&2
fi
bash infrastructure/scripts/seed_phase_1_data.sh
