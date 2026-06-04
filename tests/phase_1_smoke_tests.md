# Phase 1 Smoke Tests

Run these after installing `bedo_platform` on a Frappe site.

1. Confirm the Frappe Administrator account is available only for setup.
2. Confirm `/login` shows only username, password, and sign-in.
3. Confirm `bedo_platform.api.auth.login` authenticates through LDAP/mock LDAP and does not store plaintext passwords.
4. Confirm `bedo_platform.api.routing.get_current_user_landing_route` routes GM to `/app/gm-support-dashboard`.
5. Confirm ARD Manager routes to `/app/ard-dashboard`.
6. Confirm an ARD user cannot access `/app/srs-dashboard`.
7. Confirm GM or BEDO Global Viewer can access all department dashboards.
8. Confirm `/app/bedo-admin-users` rejects users without an admin role.
9. Confirm admin user listing never returns a password field.
10. Confirm `BEDO Security Event` records login success, login failure, logout, user creation, role change, and disablement events.
