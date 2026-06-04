# Phase 1 Architecture

Phase 1 uses Frappe Framework 15 as the core backend/admin platform and keeps the repository organized as a microservice-ready monorepo.

## Core Service

`apps/bedo_platform` is the core application service. It owns LDAP-only authentication, Frappe user synchronization, BEDO department metadata, role catalog metadata, dashboard routing, admin user management, security audit events, and placeholder Desk pages.

## Internal Modules

- `constants.py`: department keys, routes, roles, ARD team options, and seed users.
- `services`: LDAP adapter, login guard, routing guard, user management, and audit logging.
- `api`: whitelisted methods used by login, dashboards, and admin users.
- `setup`: idempotent seed routines for departments, roles, dashboards, and initial users.
- `bedo_core`: platform metadata DocTypes and the admin users page.
- department folders: placeholder dashboard pages only.

## Future Services

The `services` folder contains placeholders for future workflow, notification, reporting, and file services. They are intentionally not implemented in Phase 1.

## Deployment Shape

Local development is Docker Compose based with MariaDB and Redis. Production can keep Frappe as the core service while extracting future bounded contexts into separate service runtimes as integration needs mature.
