# Team Split

Mostafa owns identity, LDAP, users backend, roles backend, security, audit, and backend APIs.

Zeinab owns the admin dashboard UI and frontend experience.

Shared ownership includes the permission matrix and testing.

Rules to avoid Git and database conflicts:

- Do not change another owner's area without coordination.
- Do not implement Zeinab's admin dashboard UI in Phase 1.
- Keep fixture exports intentional and review role, workspace, property setter, and custom field changes before merge.
- Keep permission changes paired with smoke tests.
