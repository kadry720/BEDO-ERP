# BEDO Next.js + Frappe Redesign Plan

## 1. Current State Audit

`apps/bedo_platform` remains the Frappe backend app. It already contains LDAP authentication, Frappe user synchronization, role metadata, department metadata, user-role assignments, security events, routing logic, placeholder dashboard pages, and a Desk-based admin user page.

Keep the Frappe backend, MariaDB through Frappe, DocTypes, roles, fixtures, migrations, audit events, LDAP adapter structure, and backend service layer.

Deprecate Frappe Desk as the normal BEDO product UI. Existing Desk pages, Workspaces, profile screens, comments, activity feeds, and injected Desk cleanup JavaScript are transition artifacts only.

Do not touch ARD workflow logic, SCMDP, BMDP, KPO, RFA, RSA, Production Traveler, QC workflows, file vault, project workflows, or any business workflow DocTypes in this phase.

## 2. Target Architecture

The target runtime is:

```text
Browser
  -> Next.js bedo-web
  -> signed server-to-server BFF calls
  -> Frappe bedo_platform
  -> MariaDB through Frappe
```

Next.js owns the normal user interface: login, application shell, role navigation, dashboards, admin users, profile, forbidden, and access-not-configured pages.

Frappe owns identity, roles, departments, route permissions, technical Desk access decisions, audit logs, migrations, and future workflow foundations.

## 3. Data-Minimization Plan

Store only necessary user identity and access metadata: username, first name, optional middle name, last name, email only where Frappe/admin management requires it, phone number, linked Frappe user, primary department, roles, enabled status, last login if available, and last LDAP sync if implemented.

Never store plaintext passwords, password hashes in custom BEDO DocTypes, LDAP bind passwords, LDAP internals, session cookies, CSRF tokens, profile photos, attachments, comments, activity timeline data, HR/private data, personal documents, addresses, national IDs, birth dates, gender, or salary.

Keep `BEDO Department`, `BEDO Role Catalog`, `BEDO User Role Assignment`, `BEDO Module Access`, and `BEDO Security Event`. Add a minimal `BEDO User Profile` only if Frappe `User` plus role assignments becomes insufficient.

## 4. Authentication and Session Plan

Authentication is LDAP-only for business users.

Initial seeded users:
- `gm`
- `ard.manager`

The `gm` user is explicitly assigned `BEDO User Administrator`, so this specific account can access `/admin/users`. GM/global viewer roles do not automatically grant user administration.

Next.js `/login` accepts username and password only. The browser sends credentials to a Next.js server route. The server route calls Frappe over a signed server-to-server request. Frappe authenticates LDAP, validates local BEDO access metadata, and returns only safe user context.

Next.js maintains its own HttpOnly application session cookie containing safe signed context. The browser never receives Frappe API secrets, LDAP secrets, Frappe session IDs, backend tokens, database credentials, or service credentials.

## 5. Server-to-Server Authentication

Next.js and Frappe share `BEDO_WEB_SERVICE_SECRET`, stored only in server-side environment/site config.

Every server-to-server request includes:
- `X-BEDO-Service: bedo-web`
- `X-BEDO-User`, empty during login and set to the safe Frappe user id after login
- `X-BEDO-Timestamp`
- `X-BEDO-Nonce`
- `X-BEDO-Signature`

The signature is HMAC-SHA256 over service, user, timestamp, nonce, HTTP method, path, and SHA256 body hash. Frappe rejects missing signatures, stale timestamps, replayed nonces, bad signatures, disabled users, and unauthenticated service requests.

## 6. Frappe Desk Restriction Plan

Frappe Desk is technical-admin only.

Allowed Desk users:
- built-in `Administrator`
- `BEDO System Administrator`

Not automatically allowed:
- GM
- GM/global viewer
- ARD Manager
- SRS Manager
- department managers
- normal employees
- BEDO User Administrator unless also assigned technical system administrator

Non-technical users trying `/app` or `/desk` are redirected to the Next.js app or blocked with a clean response. This is enforced server-side, not by hiding UI elements.

## 7. Next.js Frontend Pages

Required pages:
- `/login`
- `/gm`
- `/srs`
- `/ard`
- `/ard/blueprint`
- `/ard/validation`
- `/ard/scmdp`
- `/ard/coordination`
- `/command-center`
- `/production`
- `/qc`
- `/operations`
- `/admin/users`
- `/profile`
- `/forbidden`
- `/access-not-configured`

All department dashboards remain empty placeholders in this phase. The only functional dashboard in this phase is `/admin/users`.

## 8. Frappe Backend APIs

Browser-facing Next.js route handlers call these Frappe APIs server-to-server:
- `bedo_platform.api.web.login`
- `bedo_platform.api.web.logout`
- `bedo_platform.api.web.me`
- `bedo_platform.api.web.get_landing_route`
- `bedo_platform.api.web.ensure_route_access`
- `bedo_platform.api.web.get_admin_bootstrap`
- `bedo_platform.api.web.list_users`
- `bedo_platform.api.web.create_user`
- `bedo_platform.api.web.assign_roles`
- `bedo_platform.api.web.set_user_enabled`
- `bedo_platform.api.web.get_my_profile`
- `bedo_platform.api.web.update_my_profile`
- `bedo_platform.api.web.list_security_events`

Every API validates the service signature and user authorization server-side.

## 9. Role-Based Access Plan

Department visibility:
- GM/global viewer can view all department dashboards.
- ARD users can view only ARD routes.
- SRS users can view only `/srs`.
- Command Center users can view only `/command-center`.
- Production users can view only `/production`.
- QC users can view only `/qc`.
- Operations users can view only `/operations`.

Admin visibility:
- `/admin/users` requires explicit `BEDO User Administrator` or `BEDO System Administrator`.
- `gm` has this explicitly.
- Other GM/global viewer users do not get admin automatically.

Technical visibility:
- Frappe Desk requires `Administrator` or `BEDO System Administrator`.

In this phase, permissions control only route/module visibility, admin access, and technical Frappe Desk access. Business workflow permissions are not implemented.

## 10. Admin Dashboard Plan

`/admin/users` includes sections/tabs:
- Users
- Roles
- Role Profiles
- Department Access
- Module Access / Permissions
- Security Logs

Users is functional. Other sections expose current metadata/read-only placeholders where backend data exists, without implementing workflow permissions.

## 11. UI/UX Plan

The UI is a custom BEDO industrial enterprise shell with a left sidebar, top bar, role-filtered navigation, concise cards, clean tables, accessible forms, and no Frappe branding or social/profile clutter.

Dashboards use placeholder cards only. No ARD flowchart or workflow behavior appears in this phase.

## 12. Implementation Milestones

1. Add signed Frappe web APIs and Desk restriction.
2. Create `apps/web/bedo-web` with Next.js, TypeScript, and Tailwind.
3. Build login, app session, middleware, and route guards.
4. Build placeholder department dashboards.
5. Build functional `/admin/users`.
6. Build simplified `/profile`.
7. Run backend/frontend/security tests.
8. Push branch without opening a PR.

## 13. Testing Plan

Backend tests cover LDAP login, generic failures, route access, explicit admin assignment, non-admin denial, Desk blocking, service-signature validation, and safe audit events.

Frontend tests cover unauthenticated redirects, login UI fields, role landing routes, allowed navigation, forbidden routes, `/admin/users` access, profile fields, and absence of password/secrets in rendered output.

Integration tests cover Next-to-Frappe signed calls, secure session behavior, logout, and direct Desk blocking for normal users.
