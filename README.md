# BEDO ERP

BEDO ERP is the repository for BEDO's internal enterprise platform. The active backend app is the Frappe app `bedo_platform` under `apps/bedo_platform`; the normal user-facing application is moving to the Next.js app `bedo-web` under `apps/web/bedo-web`.

## Phase 1 Scope

- Frappe v15 custom app named `bedo_platform`.
- Next.js TypeScript frontend named `bedo-web`.
- MariaDB-backed Frappe site setup.
- LDAP-only business login with username and password only.
- Frappe-native users, roles, DocTypes, fixtures, patches, and migrations.
- BEDO department metadata, role catalog metadata, dashboard routing, route guard APIs, and security audit events.
- Admin user management foundation at `/admin/users` in the Next.js app.
- Active Next.js dashboard routes for GM Support Office, SRS, and Command Center.
- Placeholder-only routes may exist for ARD, Production, QC, and Operations, but no workflow logic is active there.
- Frappe Desk access restricted to technical administrators.

Business workflow permissions and workflow DocTypes are intentionally empty in this phase. Do not implement ARD process logic from visual flowcharts; those diagrams are known to be incorrect. Later ARD workflow logic must come from Chapter 4 and Chapter 6 text only.

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
  web/
    bedo-web/
      app/
      components/
      features/
      lib/
      server/
      styles/
      tests/
```

## Environment

Copy the template and replace placeholders locally:

```bash
cp .env.example .env
```

Required LDAP and seed variables:

- `BEDO_ENV` (`local`, `development`, `test`, `staging`, or `production`)
- `LDAP_URI`
- `LDAP_BASE_DN`
- `LDAP_BIND_DN`
- `LDAP_BIND_PASSWORD`
- `LDAP_USER_SEARCH_FILTER`
- `LDAP_USE_TLS`
- `LDAP_CERT_REQUIRED`
- `BEDO_SEED_DEFAULT_PASSWORD` or per-user seed password variables such as `BEDO_SEED_GM_PASSWORD`
- `BEDO_WEB_SERVICE_SECRET`
- `BEDO_WEB_SESSION_SECRET`
- `BEDO_SESSION_REDIS_URL` for multi-process session conflict tracking
- `FRAPPE_INTERNAL_URL`

Use `BEDO_LDAP_ADAPTER=mock` only for development. Production should use `ldaps://` with certificate validation enabled.

## Local Setup

Start the local infrastructure:

```bash
docker compose up -d mariadb redis-cache redis-queue redis-socketio frappe
```

The `frappe` container now bootstraps the bench, creates the site if needed, runs migrations, seeds phase 1 data, and then starts the Frappe processes automatically.

Open a shell in the Frappe container if you need to run manual commands:

```bash
docker compose exec frappe bash
```

If you need to bootstrap manually, use:

```bash
bash /workspace/BEDO-ERP/infrastructure/scripts/init_project.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/init_site.sh
```

Run migrations and seed metadata:

```bash
bash /workspace/BEDO-ERP/infrastructure/scripts/run_migrations.sh
bash /workspace/BEDO-ERP/infrastructure/scripts/seed_phase_1_data.sh
```

Start the Next.js app from another terminal:

```bash
cd apps/web/bedo-web
npm install
npm run dev
```

Open the BEDO app at `http://localhost:3000`. The Frappe backend remains at `http://localhost:8000` for technical administrators only.

## LDAP Setup

`bedo_platform` reads LDAP settings from site config or environment variables. LDAP bind credentials and user passwords must never be committed. Business users are authenticated only through LDAP; passwords are not stored in Frappe `User`.

For development, set:

```bash
BEDO_LDAP_ADAPTER=mock
BEDO_MOCK_LDAP_PASSWORD_GM=<local-only-password>
BEDO_SEED_DEFAULT_PASSWORD=<local-only-seed-password>
```

For production, wire `LDAP_URI`, bind settings, TLS flags, and a production provisioning adapter as needed. If LDAP provisioning is unavailable, user creation will fail cleanly rather than storing local passwords.

## Seed Data

The `after_install` and `after_migrate` hooks seed departments, roles, role catalog metadata, dashboard workspaces, and module access metadata.

Initial users are synced only when explicit seed password variables are present. Set `BEDO_SEED_DEFAULT_PASSWORD` for all seed users in local development, or set per-user variables such as `BEDO_SEED_GM_PASSWORD`. No password fallback is embedded in code.

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
- Route visibility is checked server-side through `bedo_platform.api.web` and mirrored in Next.js route guards.
- User administration APIs require explicit `BEDO User Administrator` or `BEDO System Administrator` roles. The initial `gm` user has `BEDO User Administrator` explicitly assigned; GM/global viewer status alone is not enough.
- Next.js calls Frappe with signed server-to-server requests using `BEDO_WEB_SERVICE_SECRET`. The browser never receives Frappe API secrets, LDAP secrets, Frappe session IDs, backend tokens, or database credentials.
- All `bedo_platform.api.web` methods are protected by the signed service-auth wrapper even though Frappe exposes them with `allow_guest=True` for server-to-server calls.
- Login lockout tracks username and username+IP counters with generic user-facing errors.
- Session conflict state uses Redis through `BEDO_SESSION_REDIS_URL` when configured, with an in-memory fallback for local development only.
- Security events are append-only for project deletion; project deletion no longer removes `BEDO Security Event` rows.
- `BEDO_ENV=staging` or `BEDO_ENV=production` rejects placeholder secrets during startup.

## Production Sequence

1. Build the images.
2. Run migrations once.
3. Seed reference data once with explicit seed variables.
4. Start Frappe and Next.js services.
5. Run smoke tests against `/api/health`, login, project listing, and SRS workflow read paths.

## Deferred Hardening

- Full project soft delete is deferred because project deletion touches workflow/trainer relations and needs a dedicated migration and UI pass.
- A large `project_service.py` split is deferred to avoid changing SRS workflow behavior in this hardening pass.
- Broader project visibility query rewrites and polling consolidation are deferred until there is a larger contract test suite.

## Git Workflow

Do not commit directly to `main`. Use review branches by scope, for example:

```bash
git checkout -b codex/frappe-foundation
git checkout -b codex/ldap-auth
git checkout -b codex/admin-users
```

Open draft pull requests for review before merging.
