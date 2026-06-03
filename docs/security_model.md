# Security Model

## Authentication Model

BEDO ERP uses Frappe's native User, Role, Session, and LDAP facilities. BEDO-specific services add profile validation, role checks, security settings, and audit logging around protected APIs.

## LDAP Model

LDAP configuration is managed through Frappe LDAP Settings. The Phase 1 LDAP service checks whether settings are configured and whether the configured server endpoint is reachable without exposing bind passwords or domain secrets. LDAP user synchronization creates or updates the BEDO User Profile for the current authenticated user and can apply future LDAP group to Frappe role mappings.

## Local Emergency Admin Model

`BEDO Security Settings` supports local login for system administrators as an emergency path. Local login for normal users can be disabled independently. LDAP passwords are never stored in BEDO ERP.

## Roles and Permissions Model

BEDO System Admin can manage all Phase 1 records and settings. BEDO GM can view users and audit logs but cannot edit security settings. BEDO Department Manager can view users in their own department only. BEDO Engineer can view only their own profile. BEDO Viewer can access placeholder pages.

## Audit Logging Model

BEDO Access Audit Log records login success, login failure, logout, session expired, and permission denied events where Frappe hooks or service entry points provide reliable event context.

## Session Security Model

Frappe remains responsible for sessions and cookies. BEDO services log session events where possible and expose only safe session context to the frontend.

## Secrets Management Model

Secrets must be supplied through environment variables, `.env`, or Frappe site configuration. Database passwords, LDAP bind passwords, local admin passwords, and private keys must never be committed or returned by APIs.
