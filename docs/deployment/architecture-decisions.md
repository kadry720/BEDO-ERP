# BEDO Cloud Deployment Architecture Decisions

## Decision Summary

BEDO should deploy as:

- Vercel for `apps/web/bedo-web`.
- Railway for Frappe web, worker, scheduler, and socket.io/realtime processes.
- Railway MariaDB/MySQL-compatible database for the Frappe primary database.
- Railway Redis for Frappe cache, queue, and socket.io.
- A TLS Redis provider reachable from Vercel for the Next.js active-session registry.
- Neon is not used for the Frappe primary database.

## Neon Compatibility Result

Neon cannot host the primary Frappe database for this repository.

The repository is wired for Frappe v15 with MariaDB:

- `docker-compose.yml` provisions `mariadb:10.6`.
- `infrastructure/scripts/init_site.sh` uses `bench new-site` with MariaDB root credentials.
- `infrastructure/scripts/init_project.sh` sets MariaDB and Redis bench configuration.
- Existing Frappe site creation, migrations, and tests assume Frappe's MariaDB data layer.

Neon is PostgreSQL. This repo does not contain a tested Frappe PostgreSQL migration path, and the deployment work must not rewrite the Frappe persistence layer without proven framework support and full regression tests.

## Neon Optional Use

Neon can be considered later only for a separate auxiliary PostgreSQL workload, such as analytics, reporting, or an audit mirror. That would require a new integration boundary, async replication/export logic, access controls, retention rules, and tests. It is not part of the required production deployment path.

## Recommended Architecture

```text
Browser
  -> Vercel Next.js app
  -> signed HTTPS service calls using BEDO_WEB_SERVICE_SECRET
  -> Railway Frappe web process
  -> Railway MariaDB/MySQL-compatible primary database
  -> Railway Redis cache/queue/socketio

Vercel Next.js
  -> external TLS Redis for active-session and login-conflict state
```

Frappe files, private files, public files, generated assets, and site configuration must live on a Railway persistent volume mounted at `/workspace/frappe-bench/sites` unless object storage is introduced deliberately. Frappe bench code, Python dependencies, and the virtualenv are built into the image so they do not consume persistent volume space.

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Neon as primary Frappe database | Rejected | Frappe setup in this repo is MariaDB-based; Neon is PostgreSQL. |
| Vercel calling Docker hostnames such as `http://frappe:8000` | Rejected | Vercel cannot resolve Docker Compose internal hostnames. Use the Railway HTTPS backend URL. |
| In-memory Next session registry in production | Rejected | Vercel serverless instances do not share memory and can be replaced at any time. Production now fails if Redis is missing. |
| Running Frappe init, migrate, and seed on every boot | Rejected | Boot should be runtime-only. Init/migrate/seed are one-off commands. Safe seed does not reset passwords unless explicitly requested. |
| Exposing Frappe secrets to the browser | Rejected | Browser calls stay on Next routes. Next signs server-to-server calls to Frappe. |

## Public Backend Security Impact

Railway will expose the Frappe web process through HTTPS so Vercel can reach it. That public backend must keep BEDO service endpoints protected by signed HMAC headers:

- `BEDO_WEB_SERVICE_SECRET` must match on Vercel and Railway.
- The secret must never be exposed through `NEXT_PUBLIC_*`.
- Browser code should call Next routes only.
- Frappe should reject unsigned or stale service requests.
- Railway should use HTTPS and a stable public domain.

## Session State on Vercel

The current implementation keeps active-session conflict state in the Next layer. Because Vercel serverless cannot rely on process memory, production requires `BEDO_SESSION_REDIS_URL`.

Selected option:

- Use a TLS Redis provider reachable from Vercel for Next session registry data.
- Keep Railway Redis internal for Frappe cache, queue, and socket.io.
- Do not use the memory fallback outside local/test/dev.

Future option:

- Move active-session registry operations to signed Frappe service APIs so session state lives fully on Railway. That is feasible but larger than this deploy-ready hardening pass and needs targeted tests for activate, retire, challenge, allow, deny, and status flows.
