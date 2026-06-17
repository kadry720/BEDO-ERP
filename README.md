# BEDO ERP

BEDO ERP is BEDO's internal enterprise platform. The active stack is a Next.js application (`apps/web/bedo-web`) in front of a Frappe v15 app (`apps/bedo_platform/bedo_platform`) backed by MariaDB and Redis.

## Architecture

```text
Browser
  -> Next.js bedo-web
  -> signed HMAC service calls with BEDO_WEB_SERVICE_SECRET
  -> Frappe bedo_platform
  -> MariaDB and Redis
```

The browser receives only a signed, HTTP-only `bedo_session` cookie from Next.js. It never receives Frappe API secrets, database passwords, service secrets, Redis URLs, or raw Frappe session credentials.

## One-Command Local Deployment

From a fresh clone:

```bash
./scripts/bedo up
```

The command creates `.env` if missing, generates local secrets, builds the Next.js production image, starts MariaDB/Redis/Frappe/Next, runs Frappe initialization, runs migrations, runs safe seed data, and prints the local URL plus bootstrap account information.

Default local URL:

```text
http://localhost:3000
```

## Generated Secrets

`scripts/generate_env.py` creates `.env` from `.env.example` only when `.env` is missing. It generates high-entropy local values for:

- `MARIADB_ROOT_PASSWORD`
- `MARIADB_PASSWORD`
- `FRAPPE_ADMIN_PASSWORD`
- `BEDO_WEB_SERVICE_SECRET`
- `BEDO_WEB_SESSION_SECRET`
- `BEDO_SEED_DEFAULT_PASSWORD`
- `BEDO_SEED_GM_PASSWORD`

Existing `.env` files are never overwritten unless you explicitly run:

```bash
python scripts/generate_env.py --force
```

Do not commit `.env`.

## Bootstrap Credentials

Local seed users are created only when missing. The initial bootstrap user is:

```text
Username: gm
Password: shown by ./scripts/bedo credentials
```

To print the local bootstrap credentials again:

```bash
./scripts/bedo credentials
```

Seed passwords are not reapplied to existing users on startup. To intentionally reset seed user passwords, set:

```bash
BEDO_FORCE_SEED_PASSWORD_RESET=1
```

Then run the Frappe initialization/seed path again.

## Auth Model

The active authentication model is database-backed Frappe password auth:

- Users sign in to the Next.js app with BEDO username and password.
- Next.js calls Frappe through signed HMAC service requests using `BEDO_WEB_SERVICE_SECRET`.
- Frappe verifies passwords through its password APIs.
- Next.js issues a signed HTTP-only `bedo_session` cookie using `BEDO_WEB_SESSION_SECRET`.
- Redis tracks active sessions and login-conflict challenges. Local development can fall back to memory.
- Logout retires the active session and writes a retired-session tombstone so stale signed cookies cannot reactivate.

LDAP is not required for the active setup. A future LDAP integration should be added as an optional integration and must not expose LDAP bind credentials to the browser.

## Common Commands

```bash
./scripts/bedo up
./scripts/bedo down
./scripts/bedo logs
./scripts/bedo doctor
./scripts/bedo credentials
./scripts/bedo reset-local
```

`reset-local` removes local Docker containers and volumes. It leaves `.env` unchanged.

## Tests

Frontend:

```bash
cd apps/web/bedo-web
npm run typecheck
npm run test:unit
```

Backend:

```bash
PYTHONPATH=apps/bedo_platform pytest apps/bedo_platform/bedo_platform/tests
```

Compose validation:

```bash
docker compose config
./scripts/bedo doctor
```

## LAN Deployment

`scripts/generate_env.py` derives `BEDO_WEB_PUBLIC_URL` and `BEDO_WEB_ALLOWED_DEV_ORIGINS` for localhost and, when detectable, the current LAN IP.

If Next rejects an IP/origin, edit `.env` and add the full origin:

```text
BEDO_WEB_ALLOWED_DEV_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.50:3000
BEDO_WEB_PUBLIC_URL=http://192.168.1.50:3000
```

Restart:

```bash
./scripts/bedo down
./scripts/bedo up
```

## Cloud Deployment

BEDO is prepared for a split cloud deployment:

| Layer | Recommended platform | Notes |
| --- | --- | --- |
| Next.js frontend | Vercel | Root directory: `apps/web/bedo-web`; install `npm ci`; build `npm run build`. |
| Frappe web | Railway | Uses `infrastructure/railway/frappe.Dockerfile` and `bash infrastructure/railway/start-web.sh`. |
| Frappe worker | Railway | Use start command `bash infrastructure/railway/start-worker.sh`. |
| Frappe scheduler | Railway | Use one scheduler service with `bash infrastructure/railway/start-scheduler.sh`. |
| Frappe socket.io | Railway | Use `bash infrastructure/railway/start-socketio.sh` when realtime/socket.io is needed. |
| Primary database | Railway MariaDB/MySQL-compatible service | Neon/PostgreSQL is not compatible with this repo's Frappe primary database. |
| Frappe Redis | Railway Redis | Cache, queue, and socket.io Redis. |
| Next session registry | TLS Redis reachable from Vercel | Required in production through `BEDO_SESSION_REDIS_URL`; memory fallback is rejected in production. |
| Frappe files/site config | Railway volume | Mount at `/workspace/frappe-bench`. |

Start with:

- [Architecture decisions](docs/deployment/architecture-decisions.md)
- [Environment matrix](docs/deployment/cloud-env-matrix.md)
- [Manual interventions](docs/deployment/manual-interventions.md)
- [Vercel/Railway/Neon runbook](docs/deployment/vercel-railway-neon.md)

Generate ignored cloud env files:

```bash
python scripts/cloud/generate-cloud-env.py --force \
  --vercel-url https://your-vercel-domain.vercel.app \
  --railway-url https://your-railway-frappe-domain.up.railway.app \
  --session-redis-url rediss://default:password@your-session-redis.example.com:6379
python scripts/cloud/validate-cloud-env.py --vercel .env.vercel.local.generated --railway .env.railway.local.generated
```

Do not use Neon as the Frappe primary database. Neon may be useful later only for a separate analytics/reporting/audit mirror after a deliberate integration is designed and tested.

## Secret Rotation

For local development, rotate secrets by editing `.env` or regenerating it with `--force`, then restarting containers. Rotating `BEDO_WEB_SESSION_SECRET` invalidates existing browser sessions. Rotating `BEDO_WEB_SERVICE_SECRET` requires both Next and Frappe to receive the same new value.

For staging/production, use a secrets manager and set `BEDO_ENV=staging` or `BEDO_ENV=production`. Placeholder values such as `replace-me` and `change-this` are rejected for service, session, Frappe admin, and database secrets.

## Technical Frappe Port

Normal deployment exposes only Next on port `3000`. MariaDB and Redis are internal-only. Frappe is internal by default.

To temporarily expose Frappe on `localhost:8000` for technical administration:

```bash
docker compose --profile technical up -d frappe-technical-port
```

Frappe Desk remains restricted to technical administrators.

## Troubleshooting

Next rejects IP/origin:
Add the exact browser origin to `BEDO_WEB_ALLOWED_DEV_ORIGINS`, then restart `bedo-web`.

Frappe not ready:
Run `./scripts/bedo logs frappe-init frappe`. The init service owns site creation, app install, migrations, and safe seed. Runtime Frappe only starts the app.

MariaDB connection failure:
Check `docker compose ps`, then inspect `mariadb` logs. DB ports are not published by default; services communicate over the internal Compose network.

Redis/session conflict issues:
Check `redis-cache` health and `BEDO_SESSION_REDIS_URL`. If Redis is unavailable in local mode, Next falls back to in-memory tracking, which is process-local only.

Password changed then reverted:
Ensure `BEDO_FORCE_SEED_PASSWORD_RESET` is not set to `1`. Safe seed does not reset existing user passwords.

`Not authenticated` after logout/login:
Clear the browser cookie and rerun `./scripts/bedo doctor`. Logout should retire the old session and a new login should receive a new session ID.

## Security Notes

- Never commit `.env`, generated site configs, database dumps, Redis data, service secrets, or plaintext passwords.
- MariaDB and Redis are not exposed in normal deployment.
- Next-to-Frappe calls use signed HMAC requests with nonce and timestamp validation.
- `BEDO_WEB_SERVICE_SECRET` is shared only between Next and Frappe.
- Password changes use Frappe password APIs; plaintext passwords are not stored by BEDO code.
- BEDO does not enforce extra password-complexity rules; profile and admin password fields pass user-entered passwords to Frappe's password APIs.
- Profile password changes require the current password.
- Admin password resets do not require the target user's current password and retire active Next sessions for that user.
- Security audit events are created for profile updates, password changes, admin password resets, login, logout, and user administration.
- Configure rate limits and trusted proxy handling for `X-Forwarded-For` at the reverse proxy in staging/production.

## Production Sequence

Use the full [cloud runbook](docs/deployment/vercel-railway-neon.md). The short sequence is:

1. Generate and validate ignored cloud env files.
2. Create Railway Frappe services, MariaDB/MySQL-compatible database, Redis, and persistent volume.
3. Set Railway env values and run `scripts/cloud/railway-init-site.sh`.
4. Run `scripts/cloud/railway-migrate.sh`, `scripts/cloud/railway-seed-safe.sh`, and `scripts/cloud/railway-doctor.sh`.
5. Create the Vercel project from `apps/web/bedo-web` and set Vercel env values.
6. Verify `/api/health`, login, logout/login, profile password change, admin password reset, and migration status.

## Deferred Integrations

LDAP is reserved for a future optional identity-provider integration. It must be introduced behind explicit configuration, must not be required for local deployment, and must not weaken the current profile/admin password change guarantees.
