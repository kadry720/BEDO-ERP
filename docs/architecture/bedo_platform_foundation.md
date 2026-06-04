# BEDO Platform Foundation

`bedo_platform` is organized around Frappe-native extension points:

- `constants.py` owns department keys, dashboard routes, role names, ARD team options, and seed users.
- `setup/` owns idempotent seed operations for departments, roles, dashboard metadata, and initial users.
- `services/` owns LDAP authentication, login behavior, routing, user management, and security audit logging.
- `api/` exposes whitelisted server methods with permission checks.
- `bedo_core/doctype/` contains only platform metadata DocTypes.
- Department folders contain placeholder Desk pages only.

This phase deliberately does not add SCMDP, BMDP, project, BOM, KPO, RFA, RSA, or other workflow DocTypes.
