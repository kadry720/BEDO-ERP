# Final Validation

Date: 2026-06-24

## Passed

- `cd apps/web/bedo-web && npm.cmd run typecheck`
- `cd apps/web/bedo-web && npm.cmd run test:unit`
  - 57 tests passed.
- `cd apps/web/bedo-web && npm.cmd run build`
- `$env:PYTHONPATH='apps/bedo_platform'; python -m pytest apps/bedo_platform/bedo_platform/tests`
  - 114 tests passed.
- `python -m pytest tests`
  - 11 tests passed.
- `docker compose config` with required placeholder secrets:
  - `MARIADB_ROOT_PASSWORD`
  - `MARIADB_PASSWORD`
  - `FRAPPE_ADMIN_PASSWORD`
  - `BEDO_WEB_SERVICE_SECRET`
  - `BEDO_WEB_SESSION_SECRET`
- `git diff --check`

## Notes

- Raw `docker compose config` still requires real secret environment variables by design.
- No backend, API route, deployment, infrastructure, or environment-file behavior was changed for the UI refactor.

