#!/usr/bin/env bash
set -euo pipefail

BEDO_ENV_VALUE="${BEDO_ENV:-local}"
case "${BEDO_ENV_VALUE}" in
  local|dev|development|test)
    exit 0
    ;;
esac

required_vars=(
  "BEDO_WEB_SERVICE_SECRET"
  "FRAPPE_ADMIN_PASSWORD"
  "MARIADB_ROOT_PASSWORD"
)

placeholder_pattern='replace-me|change-this|local-dev-password|local-seed-password'

for name in "${required_vars[@]}"; do
  value="${!name:-}"
  if [ -z "${value}" ]; then
    echo "${name} is required when BEDO_ENV=${BEDO_ENV_VALUE}." >&2
    exit 1
  fi
  if printf '%s' "${value}" | grep -Eiq "${placeholder_pattern}"; then
    echo "${name} uses a placeholder value when BEDO_ENV=${BEDO_ENV_VALUE}." >&2
    exit 1
  fi
done
