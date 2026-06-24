# Route Inventory

## App Routes

- `/login`
- `/access-not-configured`
- `/forbidden`
- `/gm`
- `/gm/project/[...parts]`
- `/gm/projects/new`
- `/gm/projects/[projectId]`
- `/gm/projects/[projectId]/resume`
- `/gm/projects/[projectId]/trainers`
- `/gm/projects/[projectId]/items/[trainerItemId]`
- `/gm/projects/[projectId]/[projectSuffix]`
- `/gm/projects/[projectId]/[projectSuffix]/resume`
- `/gm/projects/[projectId]/[projectSuffix]/trainers`
- `/gm/projects/[projectId]/[projectSuffix]/items/[trainerItemId]`
- `/srs`
- `/srs/project/[...parts]`
- `/srs/projects/[projectId]`
- `/srs/projects/[projectId]/trainers`
- `/srs/projects/[projectId]/items/[trainerItemId]`
- `/srs/projects/[projectId]/[projectSuffix]`
- `/srs/projects/[projectId]/[projectSuffix]/trainers`
- `/srs/projects/[projectId]/[projectSuffix]/items/[trainerItemId]`
- `/ard`
- `/ard/project/[...parts]`
- `/ard/blueprint`
- `/ard/coordination`
- `/ard/scmdp`
- `/ard/validation`
- `/command-center`
- `/command-center/project/[...parts]`
- `/meetings`
- `/notifications`
- `/approvals`
- `/profile`
- `/admin/users`
- `/operations`
- `/production`
- `/qc`

## Next API Routes

- `GET /api/health`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/login-conflict`
- `GET /api/session/status`
- `GET /api/session/attention`
- `POST /api/session/conflict`
- `GET /api/session/shell-state`
- `GET|POST /api/notifications`
- `GET /api/meetings`
- `POST /api/meetings/[meetingId]/confirm`
- `GET /api/approvals`
- `GET|POST /api/approvals/[approvalId]`
- `GET|POST /api/projects`
- `GET /api/projects/assignable`
- `POST /api/projects/assign`
- `GET|PATCH|DELETE /api/projects/[projectId]`
- `POST /api/projects/[projectId]/finalize`
- `POST /api/projects/[projectId]/release-srs`
- `GET /api/projects/[projectId]/trainer-items`
- `GET|PATCH|DELETE /api/projects/[projectId]/[projectSuffix]`
- `POST /api/projects/[projectId]/[projectSuffix]/finalize`
- `POST /api/projects/[projectId]/[projectSuffix]/release-srs`
- `GET /api/projects/[projectId]/[projectSuffix]/trainer-items`
- `GET|PATCH|DELETE /api/trainer-items/[trainerItemId]`
- `GET /api/srs/flowchart`
- `POST /api/srs/workflow`
- `GET /api/srs/project-owners`
- `GET /api/srs/team-members`
- `GET /api/ard/flowchart`
- `POST /api/ard/workflow`
- `GET|POST /api/command-center/handoffs/[trainerItemId]`
- `POST /api/command-center/handoffs/[trainerItemId]/complete`
- `POST /api/command-center/handoffs/[trainerItemId]/case-3-meeting`
- `POST /api/command-center/handoffs/[trainerItemId]/handover-confirmation`
- `POST /api/workflow-resets`
- `GET /api/report-to-candidates`
- `POST /api/supplier-files/[supplierFileId]/deliver`
- `POST /api/supplier-files/[supplierFileId]/extension`
- `GET|PATCH /api/profile`
- `GET|POST|PATCH|DELETE /api/admin/users`
- `GET /api/admin/security-events`

## Protected Routing Contracts

- Route visibility is controlled by `apps/web/bedo-web/lib/routes.ts`.
- Route path helpers live in `apps/web/bedo-web/lib/route-ids.ts`.
- These files are treated as read-only for this branch.
