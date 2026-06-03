# Service Boundaries

## Current Boundary

The Frappe app is the only implemented runtime in Phase 1. It exposes whitelisted server APIs and installs DocTypes for identity, users, security, and audit.

## Future Boundaries

- `workflow-service`: future SRS/ARD workflows, process handovers, approvals, and state machines.
- `notification-service`: future email, desk, and real-time notification delivery.
- `file-service`: future managed file metadata, retention, and access rules.
- `reporting-service`: future reporting models, exports, and dashboards.

## Integration Principles

Shared identity remains centralized through Frappe users, roles, sessions, and BEDO user profiles. Future services should validate service-to-service requests and should not duplicate password or LDAP credential storage.
