# Local Setup

1. Copy `.env.example` to `.env`.
2. Replace placeholder passwords with local-only values.
3. Run `docker compose up -d mariadb redis-cache redis-queue redis-socketio frappe`.
4. The `frappe` container bootstraps the bench, creates the site if needed, runs migrations, seeds phase 1 data, and starts the Frappe processes automatically.
5. Enter the Frappe container with `docker compose exec frappe bash` only for manual maintenance.

The local site name defaults to `bedo.localhost`.
