# Phase 1 Smoke Tests

Run these after installing `bedo_erp` on a Frappe site.

1. Confirm the Administrator user can log in locally.
2. Confirm `BEDO Security Settings` exists and contains no secrets.
3. Confirm `bedo_erp.identity.api.test_ldap_configuration` returns readiness data without LDAP bind passwords.
4. Confirm `bedo_erp.identity.api.get_current_user_context` returns user, roles, department, auth source, and safe permission summary.
5. Confirm `bedo_erp.identity.api.sync_current_ldap_user_profile` creates or updates a BEDO User Profile for an LDAP-authenticated user.
6. Confirm a user without admin roles cannot call `bedo_erp.users.api.get_users_summary`.
7. Confirm a BEDO System Admin can assign a Phase 1 BEDO role.
8. Confirm deactivating a BEDO user updates `BEDO User Profile.is_active_in_bedo_erp` and does not delete the linked Frappe User.
9. Confirm access audit logs are written for service-level logout and permission denied events.
10. Confirm login success and login failure logs are written where the active Frappe hook configuration emits those events.
