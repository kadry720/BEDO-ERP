# UI Contract Baseline

## SRS Workflow

- Geometry source: `features/srs/workflowPresentation.ts`.
- Node position count: 19.
- Connector route count: 21.
- Lane count: 4.
- Never-open node IDs include approval, inactive, and display-only paths:
  - `CASES_1_2`
  - `CASES_3_4`
  - `GM_APPROVAL`
  - `GATE_1_SRS_MANAGER_APPROVAL`
  - `DUAL_GATE_APPROVAL`
  - `PMDP_DUAL_GATE_APPROVAL`
  - `EXTENSION_DEADLINE`
  - `SRS_DIRECTOR_APPROVAL`
  - `FINAL_GM_APPROVAL`
  - `ACTION_PATHS`
  - `DEADLINE_LOCKED_IN_ERP`
  - `CASE_1`
  - `CASE_2`
  - `CASE_3`
  - `CASE_4`
- Mutation route: `POST /api/srs/workflow`.
- Protected action strings:
  - `submit_deliverables`
  - `submit_pmdp_gate`
  - `request_pmdp_extension`
  - `submit_pmdp`
  - `submit_bmdp`
  - `submit_command_center`

## ARD Workflow

- Geometry source: `features/ard/ArdWorkspace.tsx`.
- Node position count: 10.
- Connector route count: 12.
- Lane count: 5.
- Mutation route: `POST /api/ard/workflow`.
- Protected action strings:
  - `schedule_internal_sync`
  - `complete_internal_sync`
  - `assign_owner`
  - `select_team`
  - `progress_review`
  - `request_interruption`
  - `confirm_procurement`
  - `choose_electronics_subcase`
  - `complete_electronics`
  - `complete_concept_proof`
  - `submit_scmdp`
- ARD interruption payload keys must remain:
  - `procurement_notes`
  - `procurement_bom_path`
  - `electronics_notes`
  - `electronics_bom_path`
  - `concept_notes`
  - `concept_report_path`

## Meetings

- Meeting list comes from `bedo_platform.api.web.list_my_meetings`.
- Confirmation route: `POST /api/meetings/[meetingId]/confirm`.
- Confirmation payload key: `{ selected_users: string[] }`.

## Notifications

- Notification list comes from `bedo_platform.api.web.list_notifications`.
- Supported actions:
  - `mark_read`
  - `mark_unread`
  - `mark_all_read`
- Action URLs are normalized through `normalizeProjectActionUrl`.

## Approvals

- Approval list comes from `bedo_platform.api.web.list_my_pending_approvals`.
- Detail/action route exists at `/api/approvals/[approvalId]`.
- POST action payloads are passed through without frontend schema changes.

## Shell

- Shell state endpoint: `GET /api/session/shell-state`.
- Session status endpoint: `GET /api/session/status`.
- Conflict endpoint: `POST /api/session/conflict`.
- Logout endpoint: `POST /api/auth/logout`.
- Badge counts are driven by `unreadNotifications`, `pendingApprovals`, and `pendingMeetings`.
