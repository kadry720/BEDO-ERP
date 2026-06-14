# Security Model

## Authentication

The browser authenticates only through the Next.js BEDO shell. Next.js calls Frappe through `bedo_platform.api.web` using signed service-auth headers. The browser never receives Frappe API secrets, LDAP bind credentials, Frappe session IDs, backend service tokens, or database credentials.

Business users authenticate through LDAP. The mock LDAP adapter is local-development only; production LDAP provisioning and password changes remain outside this implementation pass.

## Server-To-Server API

Every method in `bedo_platform.api.web` uses the central `service_api` wrapper. Frappe may expose those methods with `allow_guest=True`, but unsigned or invalid requests fail closed through HMAC validation, timestamp validation, nonce replay protection, and service-user checks.

The HMAC payload format and headers remain unchanged. Nonces are consumed only after timestamp and signature validation.

## Sessions

Next.js owns the browser session cookie. Session tokens are HMAC-signed and verified with timing-safe comparison. Malformed, tampered, expired, or badly encoded cookies return `null` instead of throwing.

Single-session conflict state is stored in Redis when `BEDO_SESSION_REDIS_URL` or `REDIS_CACHE_URL` is configured. Local development can fall back to process memory.

## Roles

Active BEDO roles are:

- BEDO Employee
- BEDO User Administrator
- BEDO Security Auditor
- BEDO System Administrator
- BEDO Global Viewer
- General Manager
- SRS Manager
- SRS Section Head
- SRS Team Leader
- SRS Engineer
- Command Center Representative

Only `BEDO System Administrator` receives Frappe Desk access. Business roles use the Next.js shell and are blocked from Desk by request-level checks.

`BEDO Global Viewer` has global visible-dashboard access. A plain `General Manager` is not automatically allowed into non-GM routes unless the account also has `BEDO Global Viewer`.

## Admin Protection

Normal admin user-management APIs hide and protect technical/system accounts such as `systemadmin`, `useradmin`, `securityauditor`, and `globalviewer`. They cannot be listed, edited, disabled, or deleted through the normal GM/admin user-management surface.

## Audit Logging

Security events are stored as UTC naive timestamps and converted at display boundaries. Project deletion does not remove `BEDO Security Event` rows.

## Production Secrets

`BEDO_ENV=staging` or `BEDO_ENV=production` rejects missing or placeholder values for required runtime secrets. Local Docker remains easy to start with `BEDO_ENV=local`, but production deployments must supply explicit secrets.
