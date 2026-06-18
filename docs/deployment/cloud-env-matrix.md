# BEDO Cloud Environment Matrix

Use `.env.vercel.example` and `.env.railway.example` as templates. Use `scripts/cloud/generate-cloud-env.py` to create ignored local generated files with strong secrets, then copy values into platform secret stores.

| Variable | Vercel | Railway | Database | Public or secret | Source | Example | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `BEDO_ENV` | Required | Required | No | Public config | User | `production` | Enables production secret checks and disables unsafe local fallback behavior. |
| `FRAPPE_INTERNAL_URL` | Required | No | No | Server-only config | User | `https://bedo-backend.up.railway.app` | Must be the Railway HTTPS Frappe web URL. Do not use `http://frappe:8000` on Vercel. |
| `BEDO_WEB_PUBLIC_URL` | Required | Required | No | Public URL | User | `https://bedo.vercel.app` | Used for redirects, origins, and backend awareness of the frontend URL. |
| `BEDO_WEB_SERVICE_SECRET` | Required | Required | No | Secret | Generated | `base64url-secret` | Must match exactly between Vercel and Railway. Protects signed Next-to-Frappe calls. |
| `BEDO_WEB_SESSION_SECRET` | Required | No | No | Secret | Generated | `base64url-secret` | Vercel-only secret for signing the HTTP-only `bedo_session` cookie. |
| `BEDO_SESSION_REDIS_URL` | Required | No | No | Secret | User/provider | `rediss://default:...@host:6379` | Required for Vercel production session state. Use TLS and a provider reachable from Vercel. |
| `NEXT_PUBLIC_BEDO_APP_NAME` | Required | No | No | Browser-public | User | `BEDO` | Safe to expose. Keep non-secret. |
| `FRAPPE_BRANCH` | No | Required | No | Public config | User | `version-15` | Frappe branch used by bench init. |
| `FRAPPE_BENCH_PATH` | No | Required | No | Public config | User | `/workspace/frappe-bench` | Image bench path. Mount Railway persistent storage at `/workspace/frappe-bench/sites`, not this whole directory. |
| `BEDO_APP_NAME` | No | Required | No | Public config | User | `bedo_platform` | Frappe app name. |
| `BEDO_APP_PATH` | No | Required | No | Public config | User | `/workspace/BEDO-ERP/apps/bedo_platform` | Path inside Railway image. |
| `FRAPPE_SITE_NAME` | No | Required | No | Public config | User | `bedo.example.com` | Frappe site directory/name. Usually use the production backend hostname or custom site name. |
| `FRAPPE_ADMIN_PASSWORD` | No | Required | No | Secret | Generated | `base64url-secret` | Needed for initial site creation. Rotate after first successful login. |
| `MARIADB_HOST` | No | Required | Yes | Secret-ish endpoint | Railway | `mysql.railway.internal` | Railway MariaDB/MySQL-compatible host. |
| `MARIADB_PORT` | No | Required | Yes | Public config | Railway | `3306` | Numeric. |
| `MARIADB_ROOT_PASSWORD` | No | Required | Yes | Secret | Railway | `railway-secret` | Needed by `bench new-site` to create the Frappe site DB/user. |
| `MARIADB_PASSWORD` | No | Required | Yes | Secret | Generated/Railway | `base64url-secret` | Local compose uses it for the DB user. Existing Frappe site DB password is stored in `site_config.json`. |
| `REDIS_CACHE_URL` | No | Required | No | Secret | Railway | `redis://default:...@redis.railway.internal:6379` | Frappe cache Redis. |
| `REDIS_QUEUE_URL` | No | Required | No | Secret | Railway | `redis://default:...@redis.railway.internal:6379` | Frappe queue Redis. |
| `REDIS_SOCKETIO_URL` | No | Required | No | Secret | Railway | `redis://default:...@redis.railway.internal:6379` | Frappe socket.io Redis. |
| `BEDO_FORCE_SEED_PASSWORD_RESET` | No | Optional | No | Public config | User | `0` | Keep `0` in production. Set `1` only for intentional seed password reset. |
| `BEDO_SEED_DEFAULT_PASSWORD` | No | Optional | No | Secret | Generated | `base64url-secret` | One-time bootstrap password for missing seed users. Safe seed does not overwrite existing users unless forced. |
| `BEDO_SEED_GM_PASSWORD` | No | Optional | No | Secret | Generated | `base64url-secret` | Optional GM-specific seed password. |
| `BEDO_SRS_DEADLINE_MODE` | No | Optional | No | Public config | User | `working_days` | Existing business setting. Do not change without business approval. |
| `FRAPPE_WORKER_QUEUES` | No | Optional | No | Public config | User | `default,short,long` | Railway worker service only. |
| `PORT` | No | Railway-provided | No | Public config | Railway | `8000` | Railway injects `PORT`. Web start command defaults to `8000` if absent. |

## Never Expose To Browser

Do not prefix these with `NEXT_PUBLIC_`:

- `FRAPPE_ADMIN_PASSWORD`
- `MARIADB_ROOT_PASSWORD`
- `MARIADB_PASSWORD`
- `REDIS_CACHE_URL`
- `REDIS_QUEUE_URL`
- `REDIS_SOCKETIO_URL`
- `BEDO_SESSION_REDIS_URL`
- `BEDO_WEB_SERVICE_SECRET`
- `BEDO_WEB_SESSION_SECRET`
- `BEDO_SEED_DEFAULT_PASSWORD`
- `BEDO_SEED_GM_PASSWORD`

## Validation

Run:

```bash
python scripts/cloud/validate-cloud-env.py --vercel .env.vercel.local.generated --railway .env.railway.local.generated
```

The validator checks required variables, production placeholders, HTTPS URLs, Vercel Redis TLS, and matching shared service secrets.
