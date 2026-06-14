# Local Setup

1. Copy `.env.example` to `.env`.
2. Keep `BEDO_ENV=local` for local Docker. Replace placeholder passwords with local-only values before sharing the environment.
3. Set `BEDO_SEED_DEFAULT_PASSWORD` for local seed users, or set per-user variables such as `BEDO_SEED_GM_PASSWORD`.
4. Run `docker compose up -d mariadb redis-cache redis-queue redis-socketio frappe`.
5. The `frappe` container bootstraps the bench, creates the site if needed, runs migrations, seeds phase 1 data, and starts the Frappe processes automatically.
6. Start the web service with `docker compose up -d bedo-web` or run `npm run dev` in `apps/web/bedo-web`.
7. Enter the Frappe container with `docker compose exec frappe bash` only for manual maintenance.

The local site name defaults to `bedo.localhost`.
The Next.js session registry uses Redis through `BEDO_SESSION_REDIS_URL` when configured and falls back to memory only for local development.
