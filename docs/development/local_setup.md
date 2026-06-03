# Local Setup

1. Copy `.env.example` to `.env`.
2. Replace placeholder passwords with local-only values.
3. Run `docker compose up -d mariadb redis-cache redis-queue redis-socketio frappe`.
4. Enter the Frappe container with `docker compose exec frappe bash`.
5. Run `bash /workspace/BEDO-ERP/infrastructure/scripts/init_project.sh`.
6. Run `bash /workspace/BEDO-ERP/infrastructure/scripts/init_site.sh`.
7. Run migrations and seeds.
8. Start the bench with `bench start`.

The local site name defaults to `bedo.localhost`.
