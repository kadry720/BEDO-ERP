# Vercel + Railway + Neon Deployment Runbook

This runbook prepares BEDO ERP for a split cloud deployment:

- Vercel hosts the Next.js frontend at `apps/web/bedo-web`.
- Railway hosts the Frappe backend, MariaDB/MySQL-compatible database, Redis, and persistent Frappe files.
- Neon is not used for the primary Frappe database because Neon is PostgreSQL and this repo's Frappe setup is MariaDB-based.

## Prerequisites

- GitHub access to `kadry720/BEDO-ERP`.
- Node.js 20 for the Next.js app.
- Python 3.11+ for helper scripts and tests.
- Docker for local compose validation.
- Vercel CLI, after account setup: `npm i -g vercel`.
- Railway CLI, after account setup: install from Railway docs.
- Neon CLI only if you later create a separate auxiliary PostgreSQL project; it is not required for the main deployment.

## Architecture

```text
Browser
  -> Vercel Next.js
  -> HTTPS signed service calls
  -> Railway Frappe web
  -> Railway MariaDB/MySQL-compatible DB
  -> Railway Redis

Vercel Next.js
  -> TLS Redis provider for BEDO session registry
```

Browser requests should go to Next.js routes. Next signs server-to-server requests to Frappe with `BEDO_WEB_SERVICE_SECRET`. Frappe rejects unsigned service calls.

## Compatibility Warning

Do not use Neon as the Frappe primary database for this repo. Frappe initialization and runtime scripts use MariaDB. A PostgreSQL migration would be a separate engineering project requiring proven Frappe support, schema migration design, and full regression tests.

Neon can be revisited later for isolated analytics or reporting, but it should not sit in the production transaction path.

## Repository Files

- Vercel config: `apps/web/bedo-web/vercel.json`
- Railway config: `railway.toml`
- Railway image: `infrastructure/railway/frappe.Dockerfile`
- Railway process commands:
  - `infrastructure/railway/start-web.sh`
  - `infrastructure/railway/start-worker.sh`
  - `infrastructure/railway/start-scheduler.sh`
  - `infrastructure/railway/start-socketio.sh`
- One-off Railway commands:
  - `scripts/cloud/railway-init-site.sh`
  - `scripts/cloud/railway-migrate.sh`
  - `scripts/cloud/railway-seed-safe.sh`
  - `scripts/cloud/railway-doctor.sh`
- Env helpers:
  - `scripts/cloud/generate-cloud-env.py`
  - `scripts/cloud/validate-cloud-env.py`

## Step 1: Generate Cloud Env Files

Run locally from the repo root:

```bash
python scripts/cloud/generate-cloud-env.py --force \
  --vercel-url https://your-vercel-domain.vercel.app \
  --railway-url https://your-railway-frappe-domain.up.railway.app \
  --session-redis-url rediss://default:password@your-session-redis.example.com:6379
```

This writes ignored files:

- `.env.vercel.local.generated`
- `.env.railway.local.generated`

Fill in Railway-provided database and Redis values in `.env.railway.local.generated`, then validate:

```bash
python scripts/cloud/validate-cloud-env.py --vercel .env.vercel.local.generated --railway .env.railway.local.generated
```

## Step 2: Create Railway Backend

In Railway:

1. Create a project connected to this GitHub repo.
2. Ensure the backend service uses `railway.toml`.
3. Add a MariaDB/MySQL-compatible database service.
4. Add a Redis service.
5. Add a persistent volume mounted at `/workspace/frappe-bench`.
6. Create separate services from the same image:
   - Frappe web: `bash infrastructure/railway/start-web.sh`
   - Worker: `bash infrastructure/railway/start-worker.sh`
   - Scheduler: `bash infrastructure/railway/start-scheduler.sh`
   - Socket.io: `bash infrastructure/railway/start-socketio.sh`

Set Railway env values from `.env.railway.local.generated`. Keep `BEDO_FORCE_SEED_PASSWORD_RESET=0` unless you intentionally want to reset seed user passwords.

## Step 3: Initialize Railway Frappe

After Railway has DB, Redis, env vars, and volume:

```bash
bash scripts/cloud/railway-init-site.sh
bash scripts/cloud/railway-migrate.sh
bash scripts/cloud/railway-seed-safe.sh
bash scripts/cloud/railway-doctor.sh
```

Expected result:

```text
Railway doctor passed: site, MariaDB, installed app, and runtime secrets are valid.
```

Do not run init/migrate/seed on every runtime boot. Runtime services should use the process commands listed above.

## Step 4: Deploy Vercel Frontend

In Vercel:

1. Import the GitHub repo.
2. Set the root directory to `apps/web/bedo-web`.
3. Install command: `npm ci`.
4. Build command: `npm run build`.
5. Output: `.next`.
6. Set env vars from `.env.vercel.local.generated`.

Required Vercel env:

```text
BEDO_ENV=production
FRAPPE_INTERNAL_URL=https://your-railway-frappe-domain.up.railway.app
BEDO_WEB_PUBLIC_URL=https://your-vercel-domain.vercel.app
BEDO_WEB_SERVICE_SECRET=<same as Railway>
BEDO_WEB_SESSION_SECRET=<Vercel-only secret>
BEDO_SESSION_REDIS_URL=rediss://...
NEXT_PUBLIC_BEDO_APP_NAME=BEDO
```

Production will fail loudly if `BEDO_SESSION_REDIS_URL` is unavailable, because in-memory session conflict tracking is unsafe on Vercel serverless.

## Step 5: Verify Deployment

Run:

```bash
curl https://your-vercel-domain.vercel.app/api/health
```

Expected:

```json
{
  "status": "ok",
  "app": "bedo-web",
  "timestamp": "2026-06-17T00:00:00.000Z",
  "frappe": {
    "status": "ok",
    "database": "ok",
    "cache": "ok",
    "app": "bedo_platform"
  }
}
```

Then verify in the browser:

1. Login with a bootstrap/admin account.
2. Logout.
3. Login again.
4. Change your own profile password.
5. Logout and login with the new password.
6. Have an admin reset another user's password.
7. Confirm the reset user must login again.

## Rollback Plan

Vercel:

- Promote the previous successful deployment in the Vercel dashboard.
- Restore the previous env values if the failure came from secret rotation.

Railway:

- Redeploy the previous successful commit/image.
- Keep the volume attached; do not delete `/workspace/frappe-bench`.
- If a migration caused the issue, restore the database backup and matching volume snapshot.

Database/files:

- Restore MariaDB backup first.
- Restore Frappe files/site volume snapshot second.
- Redeploy backend services.
- Run `scripts/cloud/railway-doctor.sh`.

## Backup Plan

Back up:

- MariaDB database.
- `/workspace/frappe-bench/sites/<site>/private`.
- `/workspace/frappe-bench/sites/<site>/public`.
- `/workspace/frappe-bench/sites/<site>/site_config.json`.

At minimum:

- Daily DB backups.
- Daily volume/file backups.
- Backup before every migration.
- Test restore in a staging Railway project.

## Secret Rotation Plan

`BEDO_WEB_SERVICE_SECRET`:

1. Set the new value in Railway and Vercel.
2. Deploy/restart Railway Frappe web.
3. Redeploy Vercel.
4. Verify `/api/health`.

`BEDO_WEB_SESSION_SECRET`:

1. Set the new value in Vercel.
2. Redeploy Vercel.
3. Expect existing browser sessions to become invalid.

Database and Redis:

1. Rotate in provider dashboard.
2. Update Railway env.
3. Restart Frappe services.
4. Run `scripts/cloud/railway-doctor.sh`.

Bootstrap passwords:

1. Login once.
2. Change the password through the app or Frappe admin path.
3. Keep `BEDO_FORCE_SEED_PASSWORD_RESET=0`.

## Production Hardening Checklist

- `BEDO_ENV=production` on Vercel and Railway.
- No placeholder secrets.
- `BEDO_WEB_SERVICE_SECRET` matches between platforms.
- `BEDO_WEB_SESSION_SECRET` exists only on Vercel unless a future backend feature needs it.
- Vercel `BEDO_SESSION_REDIS_URL` uses `rediss://`.
- Railway DB and Redis are not exposed publicly unless strictly required.
- Railway Frappe uses HTTPS public domain for Vercel calls.
- Frappe volume is mounted at `/workspace/frappe-bench`.
- Backups are configured and restore-tested.
- Frappe Desk is limited to technical administrators.
- Seed password reset is disabled after bootstrap.
- Custom domains and SSL are verified.

## Troubleshooting

Vercel build fails:

- Confirm root directory is `apps/web/bedo-web`.
- Confirm install command is `npm ci`.
- Run locally: `cd apps/web/bedo-web && npm run build`.

Railway build fails:

- Confirm `railway.toml` is used.
- Confirm Dockerfile path is `infrastructure/railway/frappe.Dockerfile`.
- Inspect build logs for package install or permission failures.

Frappe cannot connect to DB:

- Check `MARIADB_HOST`, `MARIADB_PORT`, and root password.
- Confirm the DB service is MariaDB/MySQL-compatible, not Neon/PostgreSQL.
- Run `bash scripts/cloud/railway-doctor.sh`.

Redis unavailable:

- Check `REDIS_CACHE_URL`, `REDIS_QUEUE_URL`, and `REDIS_SOCKETIO_URL` on Railway.
- Check `BEDO_SESSION_REDIS_URL` on Vercel for the Next session registry.
- Use `rediss://` for Vercel production Redis.

Service auth fails:

- Confirm `BEDO_WEB_SERVICE_SECRET` matches exactly on Vercel and Railway.
- Confirm Vercel calls `FRAPPE_INTERNAL_URL` over HTTPS.
- Redeploy both sides after changing the secret.

CORS/origin problems:

- Keep browser calls on Next routes.
- Set `BEDO_WEB_PUBLIC_URL` to the exact Vercel/custom-domain origin.
- Do not add hard-coded personal IPs to `next.config.mjs`.

`Not authenticated`:

- Clear browser cookies.
- Confirm Vercel session Redis is reachable.
- Confirm login returns a `bedo_session` HTTP-only cookie.

`already signed in` after logout:

- Confirm logout calls `/api/auth/logout`.
- Confirm Redis session registry is available.
- Confirm Vercel is not falling back to memory; production now rejects that path.

Password changed then reverted:

- Ensure `BEDO_FORCE_SEED_PASSWORD_RESET=0`.
- Do not run seed with forced reset after user password changes.

Frappe site not found:

- Confirm the Railway volume is mounted at `/workspace/frappe-bench`.
- Run `bash scripts/cloud/railway-init-site.sh`.
- Confirm `FRAPPE_SITE_NAME` matches the site directory.

Missing persistent files:

- Confirm public/private files are under the mounted Frappe sites volume.
- Restore from file backup if the volume was missing during a deploy.

## Smoke Tests

After every production deployment:

```bash
curl https://your-vercel-domain.vercel.app/api/health
```

Then manually verify:

- Signed service call through Next health endpoint.
- Login.
- Logout then login.
- Profile password change persistence.
- Admin password reset.
- Migration status through `scripts/cloud/railway-doctor.sh`.
