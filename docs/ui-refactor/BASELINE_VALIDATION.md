# Baseline Validation

Date: `2026-06-24`

## Frontend

- `npm.cmd ci`
  - Result: pass
  - Output summary: added 117 packages, audited 118 packages, 0 vulnerabilities.
- `npm.cmd run typecheck`
  - Result: pass
  - Output summary: `tsc --noEmit` exited 0.
- `npm.cmd run test:unit`
  - Result: pass
  - Output summary: 52 tests, 52 passed, 0 failed.
- `npm.cmd run build`
  - Result: pass
  - Output summary: Next.js 16.2.7 production build compiled, generated 48 static pages, exited 0.

## Backend And Repository

- `$env:PYTHONPATH='apps/bedo_platform'; python -m pytest apps/bedo_platform/bedo_platform/tests`
  - Result: pass
  - Output summary: 114 tests, 114 passed.
- `python -m pytest tests`
  - Result: pass
  - Output summary: 11 tests, 11 passed.
- `docker compose config`
  - Raw local result: failed because required environment variable `MARIADB_PASSWORD` was not set.
  - Error: `required variable MARIADB_PASSWORD is missing a value`.
  - Follow-up syntax check with temporary placeholder shell variables for all required compose secrets:
    - `MARIADB_ROOT_PASSWORD`
    - `MARIADB_PASSWORD`
    - `FRAPPE_ADMIN_PASSWORD`
    - `BEDO_WEB_SERVICE_SECRET`
    - `BEDO_WEB_SESSION_SECRET`
  - Follow-up result: pass, compose configuration rendered successfully.
- `git diff --check`
  - Result: pass
  - Output summary: no whitespace or conflict-marker issues.

## Notes

- PowerShell blocks `npm.ps1` on this machine, so Node commands were run through `npm.cmd`.
- The Docker Compose raw failure is a local environment setup issue, not a syntax failure in the compose file.
