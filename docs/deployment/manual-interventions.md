# BEDO Cloud Deployment Manual Interventions

Codex can prepare repository files, scripts, templates, and validation. The steps below require your accounts, credentials, billing decisions, or platform UI access.

## 1. Create Or Log In To Platform Accounts

| Step | Why required | Place | CLI option | Verify | What can go wrong |
| --- | --- | --- | --- | --- | --- |
| Vercel account/login | Vercel hosts `apps/web/bedo-web`. | Vercel dashboard | `vercel login` | `vercel whoami` prints your account. | Wrong team selected; missing GitHub access. |
| Railway account/login | Railway hosts Frappe, MariaDB/MySQL-compatible DB, Redis, and volume. | Railway dashboard | `railway login` | `railway whoami` prints your account. | Wrong workspace selected; plan lacks volumes. |
| Neon account/login | Only needed for future auxiliary PostgreSQL use. | Neon dashboard | `neon auth` | Neon CLI lists projects. | Do not create Neon for the primary Frappe DB; it is incompatible with this deployment. |

## 2. Connect GitHub Repository

| Step | Why required | Place | CLI option | Verify | What can go wrong |
| --- | --- | --- | --- | --- | --- |
| Connect repo to Vercel | Vercel needs GitHub access for frontend deploys. | Vercel project import | `vercel link` after login | Project root is `apps/web/bedo-web`; builds use `npm ci` and `npm run build`. | Wrong root directory builds the repo root instead of Next app. |
| Connect repo to Railway | Railway needs GitHub or CLI deploy access for backend image. | Railway project settings | `railway link` then `railway up` | Railway uses root `railway.toml` and `infrastructure/railway/frappe.Dockerfile`. | Railway may select Nixpacks unless Dockerfile config is used. |

## 3. Create Railway Services

Create separate Railway services from the same backend image:

| Service | Start command | Why required | Verify | What can go wrong |
| --- | --- | --- | --- | --- |
| Frappe web | `bash infrastructure/railway/start-web.sh` | Serves signed Frappe service API calls from Vercel. | Public Railway URL loads a Frappe response; Next `/api/health` reports `frappe.status=ok`. | Site missing; volume not mounted; wrong `PORT`; service secret mismatch. |
| Worker | `bash infrastructure/railway/start-worker.sh` | Processes queued background jobs. | Railway logs show worker listening on configured queues. | Queue Redis URL wrong; worker starts before init. |
| Scheduler | `bash infrastructure/railway/start-scheduler.sh` | Runs scheduled Frappe jobs. | Railway logs show scheduler loop. | Duplicate scheduler services cause repeated jobs. Run only one scheduler. |
| Socket.io | `bash infrastructure/railway/start-socketio.sh` | Supports Frappe realtime/socket.io if workflows need it. | Railway logs show socket.io server. | Missing Redis socket.io URL; custom routing not configured. |
| MariaDB/MySQL-compatible DB | Railway database service | Primary Frappe database. | `scripts/cloud/railway-doctor.sh` can run `select 1`. | Neon/PostgreSQL will not work as the Frappe primary DB. |
| Redis | Railway Redis service | Frappe cache, queue, and socket.io. | Frappe health reports cache `ok` through Next `/api/health`. | Reusing a Vercel public Redis for Frappe is possible but increases exposure; prefer Railway internal Redis. |
| Persistent volume | Mount at `/workspace/frappe-bench` | Stores Frappe bench, sites, private files, public files, generated assets, and site config. | Files remain after redeploy/restart. | Missing volume causes site/files to disappear after rebuild. |

## 4. Generate And Set Secrets

Run locally:

```bash
python scripts/cloud/generate-cloud-env.py --force \
  --vercel-url https://your-vercel-domain.vercel.app \
  --railway-url https://your-railway-frappe-domain.up.railway.app \
  --session-redis-url rediss://default:password@your-session-redis.example.com:6379
python scripts/cloud/validate-cloud-env.py --vercel .env.vercel.local.generated --railway .env.railway.local.generated
```

Copy the Vercel values into Vercel Project Settings -> Environment Variables.

Copy the Railway values into each Railway Frappe service. For Railway CLI after login:

```bash
railway variables set BEDO_ENV=production
railway variables set BEDO_WEB_SERVICE_SECRET=<same-value-as-vercel>
railway variables set FRAPPE_SITE_NAME=bedo.example.com
```

Verify:

- Vercel environment list contains no placeholders.
- Railway environment list contains no placeholders.
- `BEDO_WEB_SERVICE_SECRET` matches exactly in both platforms.

Common failures:

- Pasting quotes into dashboard values.
- Rotating only one side of the shared service secret.
- Setting `BEDO_WEB_SESSION_SECRET` on Railway unnecessarily.
- Using `redis://` instead of `rediss://` for Vercel session Redis.

## 5. Domains, DNS, And SSL

| Step | Why required | Place | Verify | What can go wrong |
| --- | --- | --- | --- | --- |
| Configure Vercel domain | Users need the frontend URL. | Vercel Domains | `https://your-domain` loads Next login page. | DNS points to wrong project; env `BEDO_WEB_PUBLIC_URL` still uses old domain. |
| Configure Railway backend domain | Vercel needs stable HTTPS URL for Frappe. | Railway service networking | `FRAPPE_INTERNAL_URL` in Vercel uses this URL. | HTTP-only or changing generated domain breaks service calls. |
| Configure DNS records | Custom domains require DNS ownership. | DNS provider | Vercel/Railway show verified. | CNAME/A record conflicts; stale DNS cache. |
| SSL/custom domain verification | Required for secure cookies and service calls. | Vercel/Railway dashboards | Browser shows valid HTTPS cert. | Certificate pending due wrong DNS. |

## 6. First Deploy Commands

After Railway env, DB, Redis, and volume are ready, run one-off commands from a Railway shell or CLI job:

```bash
bash scripts/cloud/railway-init-site.sh
bash scripts/cloud/railway-migrate.sh
bash scripts/cloud/railway-seed-safe.sh
bash scripts/cloud/railway-doctor.sh
```

Verify:

- `railway-doctor.sh` prints success.
- Vercel `/api/health` returns JSON with `status: ok`.
- Login works with a seed/admin user.
- Logout then login works.

Common failures:

- Running runtime web before site init.
- Missing MariaDB root credentials for `bench new-site`.
- No persistent volume at `/workspace/frappe-bench`.
- `BEDO_FORCE_SEED_PASSWORD_RESET=1` left enabled unintentionally.

## 7. Operational Decisions

You must choose:

- Railway plan with enough memory/CPU for Frappe and volume support.
- Database backup frequency and retention.
- Whether Railway volumes are enough or object storage is needed for files.
- Vercel plan and team/project ownership.
- TLS Redis provider for Vercel session registry.
- Whether Neon should be created later for a separate reporting database.

After first successful login:

- Rotate bootstrap credentials.
- Disable or rotate any one-time seed password.
- Confirm technical Frappe Desk access is limited to technical administrators.
