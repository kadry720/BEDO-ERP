# Protected Contracts

## Routes

- Existing user-facing routes remain in `docs/ui-refactor/ROUTE_INVENTORY.md`.
- New route: `/srs/ard-electronics-cases`.
- New BFF route: `GET /api/srs/ard-electronics-cases`.

## Existing BFF Contracts Kept

- `POST /api/srs/workflow`
- `POST /api/ard/workflow`
- `GET /api/meetings`
- `POST /api/meetings/[meetingId]/confirm` with `{ selected_users: string[] }`
- `GET /api/notifications`
- `POST /api/notifications`
- `GET /api/approvals`
- `GET|POST /api/approvals/[approvalId]`
- `GET /api/session/shell-state`
- `GET /api/session/status`
- `POST /api/session/conflict`
- `POST /api/auth/logout`

## New Electronics Contract

- `GET /api/srs/ard-electronics-cases` requires the exact role `SRS Electronics Section Head`.
- It calls `bedo_platform.api.web.list_srs_electronics_ard_cases`.
- It returns trainer-level rows under `{ cases: [...] }`.
- Electronics mutations continue through existing `POST /api/ard/workflow` actions:
  - `choose_electronics_subcase`
  - `complete_electronics`

## Workflow Contracts

- SRS node IDs, connector routes, action strings, and payload keys are protected by `apps/web/bedo-web/tests/ui-contract-baseline.test.ts`.
- ARD node IDs, connector routes, action strings, interruption payload keys, and Electronics mutation paths are protected by `apps/web/bedo-web/tests/ui-contract-baseline.test.ts` and `apps/web/bedo-web/tests/ard-flowchart.test.ts`.
