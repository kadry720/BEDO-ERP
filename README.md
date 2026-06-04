# BEDO ERP

BEDO ERP is the repository for BEDO's internal enterprise platform. The active Phase 1 Frappe app is `bedo_platform` under `apps/bedo_platform`.

## Phase 1 Scope

- Frappe v15 custom app named `bedo_platform`.
- MariaDB-backed Frappe site setup.
- LDAP-only business login with username and password only.
- Frappe-native users, roles, pages, DocTypes, fixtures, patches, and migrations.
- BEDO department metadata, role catalog metadata, dashboard routing, route guard APIs, and security audit events.
- Admin user management foundation at `/app/bedo-admin-users`.
- Empty dashboards for GM Support Office, SRS, ARD, Command Center, Production, QC, and Operations.
- Multiple empty ARD dashboards with no workflow logic.

Business workflow permissions and workflow DocTypes are intentionally empty in this phase. Do not implement ARD process logic from visual flowcharts; those diagrams are known to be incorrect. Future ARD workflow logic must come from Chapter 4 and Chapter 6 text only.

## Project Layout

```text
apps/
  bedo_platform/
    pyproject.toml
    bedo_platform/
      constants.py
      hooks.py
      setup/
      services/
      api/
      bedo_core/
      gm_support/
      srs/
      ard/
      command_center/
      production/
      qc/
      operations/
      public/
      templates/pages/login.html
      tests/
```

## Environment

Copy the template and replace placeholders locally:

```bash
cp .env.example .env
```

Required LDAP and seed variables:

- `LDAP_URI`
- `LDAP_BASE_DN`
- `LDAP_BIND_DN`
- `LDAP_BIND_PASSWORD`
- `LDAP_USER_SEARCH_FILTER`
- `LDAP_USE_TLS`
- `LDAP_CERT_REQUIRED`
- `BEDO_SEED_GM_PASSWORD`
- `BEDO_SEED_ARD_MANAGER_PASSWORD`

Use `BEDO_LDAP_ADAPTER=mock` only for development. Production should use `ldaps://` with certificate validation enabled.

## Local Setup

Start the local infrastructure:

```bash
docker compose up -d mariadb redis-cache redis-queue redis-socketio frappe
```

Open a shell in the Frappe container:

```bash
docker compose exec frappe bash
```

Initialize bench and install the app:

```bash
bash /workspace/BEDO-ERP/infrastructure/scripts/init_project.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/init_site.sh
```

Run migrations and seed metadata:

```bash
bash /workspace/BEDO-ERP/infrastructure/scripts/run_migrations.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/seed_phase_1_data.sh
```

Start Frappe:

```bash
cd /workspace/frappe-bench
bench start
```

## LDAP Setup

`bedo_platform` reads LDAP settings from site config or environment variables. LDAP bind credentials and user passwords must never be committed. Business users are authenticated only through LDAP; passwords are not stored in Frappe `User`.

For development, set:

```bash
BEDO_LDAP_ADAPTER=mock
BEDO_MOCK_LDAP_PASSWORD_GM=<local-only-password>
BEDO_MOCK_LDAP_PASSWORD_ARD_MANAGER=<local-only-password>
```

For production, wire `LDAP_URI`, bind settings, TLS flags, and a production provisioning adapter as needed. If LDAP provisioning is unavailable, user creation will fail cleanly rather than storing local passwords.

## Seed Data

The `after_install` and `after_migrate` hooks seed departments, roles, role catalog metadata, dashboard workspaces, and module access metadata.

Initial users are synced only when these variables are present:

- `BEDO_SEED_GM_PASSWORD`
- `BEDO_SEED_ARD_MANAGER_PASSWORD`

To require initial user creation during setup:

```bash
bench --site bedo.localhost execute bedo_platform.setup.seed_initial_users.execute --kwargs "{'strict': true}"
```

## Tests

Run standalone tests from the repository root:

```bash
PYTHONPATH=apps/bedo_platform pytest apps/bedo_platform/bedo_platform/tests
```

Run Frappe tests after installing the app on a site:

```bash
cd /workspace/frappe-bench
bench --site bedo.localhost run-tests --app bedo_platform
```

## Security Notes

- No secrets, LDAP bind passwords, local passwords, generated site configs, or plaintext user passwords belong in Git.
- Login UI exposes username and password only.
- Signup, social login, magic link, and forgot password are not implemented.
- Route visibility is checked server-side through `bedo_platform.api.routing`.
- User administration APIs require GM Support, General Manager, BEDO User Administrator, or BEDO System Administrator roles.
- Security events are recorded for login success, login failure, logout, user creation, role changes, and user disablement.

## Git Workflow

Do not commit directly to `main`. Use review branches by scope, for example:

```bash
git checkout -b codex/frappe-foundation
git checkout -b codex/ldap-auth
git checkout -b codex/admin-users
```

Open draft pull requests for review before merging.
