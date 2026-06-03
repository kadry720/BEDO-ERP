# Team Split

Mostafa owns identity, LDAP, users backend, roles backend, security, audit, and backend APIs.

Zeinab owns the admin dashboard UI and frontend experience.

Shared ownership includes the permission matrix and testing.

To avoid Git and database conflicts:

- Zeinab should not change backend auth, security, audit, or role service files without coordination.
- Mostafa should not implement dashboard UI beyond placeholders.
- Fixture changes should be exported intentionally and reviewed before merge.
- Permission changes should be tested against the Phase 1 smoke scenarios.
