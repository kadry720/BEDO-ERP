# Phase 1 Architecture

Phase 1 uses Frappe Framework 15 as the core backend/admin platform and keeps the repository organized as a microservice-ready monorepo.

## Core Service

`apps/bedo_erp` is the current core application service. It owns authentication context, LDAP integration helpers, BEDO user profiles, roles, permissions, security settings, audit logs, and minimal placeholder pages.

## Internal Modules

- `identity`: current user context, LDAP test/sync helpers, session logout handling.
- `users`: user profile lookup, department assignment, role assignment, BEDO deactivation.
- `security`: singleton security settings and authorization policies.
- `audit`: audit log creation and filtered reads.
- `admin_placeholder`: only placeholder pages for Zeinab's future UI.
- `shared`: shared constants, response helpers, and exceptions.

## Future Services

The `services` folder contains placeholders for future workflow, notification, reporting, and file services. They are intentionally not implemented in Phase 1.

## Deployment Shape

Local development is Docker Compose based with MariaDB and Redis. Production can keep Frappe as the core service while extracting future bounded contexts into separate service runtimes as integration needs mature.
