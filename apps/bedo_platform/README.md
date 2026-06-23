# BEDO Platform

`bedo_platform` is the Frappe v15 backend app for BEDO ERP. It provides signed service APIs for the Next.js frontend, MariaDB-backed workflow DocTypes, Redis-backed Frappe services, safe seed data, user administration, approvals, notifications, deadlines, meetings, and audit logging.

## Authentication

The active application login is Frappe password authentication through signed server-to-server calls from Next.js. LDAP is not required for the current runtime. Next.js owns the browser session cookie, while Frappe verifies credentials and executes backend workflow mutations.

All public web methods in `bedo_platform.api.web` must remain wrapped by the signed service-auth decorator and must call `validate_service_request()` before reading or mutating user-scoped data.

## Workflow Domains

Current backend workflow domains include:

- SRS workflow state, approvals, deadlines, and PMDP/BMDP path submissions.
- Command Center SRS-to-ARD handoffs, Case 3 Handover Meeting, Handover Confirmation, and failed-handover GM decision.
- Reusable meeting records and participants for handover, Internal ARD Sync, Progress Review, and future meeting types.
- ARD workflow instance, node state, team members, interruption requests, SCMDP submission, and supplier-order integration.
- Workflow reset service for Command Center, SRS Action Paths, and SRS Coordination.
- Supplier records for legacy Command Center supplier files and normalized ARD supplier orders.

## Important DocTypes

- `SRS Workflow Instance`
- `SRS Workflow Node State`
- `SRS Approval`
- `BEDO Command Center Handoff`
- `BEDO Meeting`
- `BEDO Meeting Participant`
- `ARD Workflow Instance`
- `ARD Workflow Node State`
- `ARD Workflow Team Member`
- `ARD Interruption Request`
- `BEDO Supplier File`
- `BEDO Supplier Order`
- `BEDO Deadline`
- `BEDO Notification`
- `BEDO Security Event`

## Scheduler Jobs

The Frappe scheduler must be running in production. It owns:

- Meeting reminders.
- Meeting automatic completion.
- Meeting overdue checks.
- Deadline reminders.
- Deadline overdue checks and extension approval creation.

Use one scheduler service in Railway with `bash infrastructure/railway/start-scheduler.sh`. Scheduler methods are intended to be idempotent under retries.

## Safe Seed Guarantees

Safe seed creates missing roles, departments, profiles, and deterministic development users without overwriting manually changed passwords or profile data. Existing passwords are only reset when `BEDO_FORCE_SEED_PASSWORD_RESET=1`.

Seeded workflow accounts include GM, SRS, Command Center, and ARD users. Replace deterministic development users with real production employee data through admin/user-management workflows or a reviewed business-data migration.

## Local Backend Checks

```bash
PYTHONPATH=apps/bedo_platform pytest apps/bedo_platform/bedo_platform/tests
```

For Docker-backed local validation, use:

```bash
./scripts/bedo up
./scripts/bedo doctor
```

## Deployment Notes

The Frappe app remains MariaDB/MySQL-compatible. Do not replace the transactional database with PostgreSQL/Neon. Railway deployment uses the Frappe web, worker, scheduler, and optional socket.io services documented in the root README and deployment runbook.
