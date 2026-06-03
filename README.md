# BEDO ERP / Industrial Follow-Up System

BEDO ERP is the Phase 1 foundation for BEDO's internal industrial follow-up system. This phase builds the authentication and administration base only. Future phases will add SRS, ARD, workflow tracking, dynamic flowcharts, handovers, approvals, dashboards, and reporting.

## Phase 1 Scope

- Frappe Framework custom app named `bedo_erp`.
- Authentication, LDAP integration foundation, user profiles, roles, permissions, audit logging, and backend APIs owned by Mostafa.
- Minimal placeholder home page and admin dashboard page owned later by Zeinab.
- Microservice-ready monorepo layout with future service placeholders.
- Docker-based local development with MariaDB and Redis.

## Architecture Overview

Frappe is the core backend/admin platform because it already provides users, roles, sessions, DocTypes, forms, list views, permissions, workspaces, hooks, migrations, and fixtures. The monorepo keeps clear service boundaries so workflow, notification, file, and reporting services can later be split out without reshaping the core application.

The current bounded contexts are:

- `identity`: login context, LDAP foundation, sessions, profile synchronization.
- `users`: user profiles, departments, BEDO role assignment, profile access rules.
- `security`: security settings and policy checks.
- `audit`: access audit logging and audit query APIs.
- `admin_placeholder`: minimal pages for Zeinab's future UI.
- `shared`: constants, errors, and response helpers.

## Local Setup

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Edit `.env` with local-only passwords and LDAP placeholders.

3. Start the local infrastructure:

```bash
docker compose up -d mariadb redis-cache redis-queue redis-socketio frappe
```

4. Open a shell in the Frappe container:

```bash
docker compose exec frappe bash
```

5. Initialize the bench:

```bash
bash /workspace/BEDO-ERP/infrastructure/scripts/init_project.sh
```

6. Create the site and install the app:

```bash
bash /workspace/BEDO-ERP/infrastructure/scripts/init_site.sh
```

7. Run migrations and seed safe Phase 1 data:

```bash
bash /workspace/BEDO-ERP/infrastructure/scripts/run_migrations.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/seed_phase_1_data.sh
```

8. Start Frappe:

```bash
cd /workspace/frappe-bench
bench start
```

## Database Initialization

The DocType schema is installed by Frappe migrations when `bedo_erp` is installed. MariaDB credentials are read from `.env` and are not committed. The app adds DocTypes for departments, BEDO user profiles, LDAP group role mapping, access audit logs, and singleton security settings.

## LDAP Notes

Configure Frappe's native `LDAP Settings` DocType in the desk or through deployment automation. The BEDO app reads LDAP settings through Frappe APIs and never returns bind passwords or domain secrets through API responses. LDAP passwords are never stored by BEDO ERP.

## Git Workflow

Use feature branches for implementation work:

```bash
git checkout -b feature/phase-1-auth-foundation
git status
git add .
git commit -m "Build Phase 1 auth foundation"
git push -u origin feature/phase-1-auth-foundation
```

Do not force push shared branches. Export fixtures after role, workspace, property setter, or custom field changes.

## Team Split

Mostafa owns identity, LDAP, users backend, roles backend, security settings, audit logging, and backend APIs. Zeinab owns the admin dashboard UI and visual frontend experience. This repository only contains minimal placeholders for Zeinab's pages.

## Security Rules

- Do not commit secrets, passwords, LDAP bind credentials, database passwords, private keys, or generated site configs.
- Keep authorization checks server-side.
- Use Frappe users, roles, sessions, LDAP settings, and permission utilities where possible.
- Permit emergency local access for system administrators only when configured.
- Do not delete Frappe users when deactivating BEDO access.
- Do not expose stack traces or internal secrets through API responses.
- Run production deployments behind HTTPS.

## Tests

Run Frappe tests after installing the app on a site:

```bash
cd /workspace/frappe-bench
bench --site bedo.localhost run-tests --app bedo_erp
```

Smoke test scenarios are documented in `tests/phase_1_smoke_tests.md`.
