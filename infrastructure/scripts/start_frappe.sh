#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/init_frappe.sh"
exec bash "${SCRIPT_DIR}/start_frappe_runtime.sh"
