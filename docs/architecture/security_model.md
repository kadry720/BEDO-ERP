# Security Model

## Authentication

Frappe's native authentication and session management remain the source of truth. BEDO ERP adds profile and policy checks around protected APIs.

## LDAP

LDAP configuration is stored in Frappe's native LDAP Settings. BEDO ERP helper APIs test readiness and synchronize the current user's BEDO profile without exposing bind credentials or storing LDAP passwords.

## Emergency Local Admin

Local login can be allowed for system administrators through `BEDO Security Settings`. Normal local user login can be disabled independently.

## Roles and Permissions

Phase 1 roles are:

- BEDO System Admin
- BEDO GM
- BEDO SRS Manager
- BEDO ARD Manager
- BEDO Department Manager
- BEDO Engineer
- BEDO Viewer

All authorization checks are enforced server-side in service functions. Frontend placeholders must not be treated as security controls.

## Audit Logging

Access audit logs record login success, login failure, logout, session expired, and permission denied events when Frappe hooks or service entry points provide the event context.

## Sessions

Frappe manages session creation, cookies, and logout. BEDO ERP stores session references in audit logs where available and exposes safe current-user context through a whitelisted API.

## Secrets

Secrets are configured through environment variables, `.env`, or Frappe site configuration. No secrets are committed to Git, returned from APIs, or stored in frontend files.
