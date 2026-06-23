# ARD Workflow Overhaul Implementation Notes

## Branch Implementation Status

This branch implements the first production-ready ARD workflow foundation:

- ARD department routing, role visibility, route checks, and deterministic safe seed users.
- Additional deterministic Command Center representative seed users.
- Sidebar utility relocation with Meetings, Notifications, Approvals, Profile, and Log out controls.
- Reusable `BEDO Meeting` and `BEDO Meeting Participant` records with reminders, overdue checks, auto-completion, `/meetings`, and signed BFF routes.
- Command Center sub-tabs with `SRS -> ARD`, Case 3 Handover Meeting, Handover Confirmation, failed-handover GM approval, Continue Anyway, and reset.
- Approval department categorization and tabs for SRS, ARD, Command Center, and Suppliers.
- Workflow reset service for Command Center, SRS Action Paths, and SRS Coordination, including downstream ARD/meeting/supplier invalidation.
- ARD workflow DocTypes, workspace route, flowchart definition, Internal ARD Sync, owner assignment, team selection, Progress Review, On Plan, interruption request, supplier-order creation, and SCMDP submission.
- Removal of workflow file browse controls and copy-path success/failure feedback.

Known remaining hardening items:

- ARD deadline ledger pause/resume accounting is partially represented through workflow state, but the full seven-working-day active-budget ledger, whole-day carryover, and overlapping blocker accounting still need deeper persistence tests before production policy enforcement.
- Notification stale-action invalidation is handled through reset superseding for workflow records, but notification rows do not yet carry a dedicated generation-validity field.
- Actual ARD section names, ARD employee roster, and Command Center roster must be supplied by the business before production seed data is final.

## Current-State Findings

- The backend already has placeholder ARD module files and Next.js routes under `/ard`, but ARD is not an active workflow module.
- `constants.py` defines the ARD department with an empty dashboard route and excludes ARD from visible departments, department roles, user routing, and seeded business roles.
- Existing SRS workflow state is centralized in `project_service.py`, which is too large for the new ARD, meeting, reset, and supplier domains.
- Existing Command Center handoff support covers SRS-to-ARD Cases 1, 2, and 3 as direct handoff decisions, but Case 3 currently routes to ARD without a meeting stage.
- Existing approvals are stored in `SRS Approval`; they do not have a normalized department/category field yet.
- Existing deadlines use `BEDO Deadline` with active, completed, and overdue states. ARD needs a budget ledger because pause/resume behavior cannot be represented safely by the current scalar deadline fields alone.
- Existing notifications are persisted in `BEDO Notification`; the model can be extended for source department, workflow generation, meeting, and reset-invalidated action links.
- Existing supplier tracking uses `BEDO Supplier File` for Command Center Case 2. The new requirement needs a generic supplier-order lifecycle that can include ARD electronics orders.

## Proposed Scope Split

The implementation is split into focused domains:

- ARD identity and routing: roles, department visibility, seeds, route checks, and module access.
- Meeting domain: meeting DocTypes, participants, reminders, completion, overdue handling, and `/meetings`.
- Command Center handover: Case 3 meeting, confirmation, failed-handover approval, and sub-tabs.
- Reset engine: transactional generation invalidation for Command Center and SRS reset targets.
- ARD workflow: workflow instance, nodes, team, owner assignment, progress review, interruptions, SCMDP.
- Deadline ledger: ARD active budget, milestone due dates, whole-day carryover, and blockers.
- Supplier orders: generic supplier records and compatibility with existing `BEDO Supplier File`.
- Notification and approval presentation: department tabs and richer cards.

## Proposed DocTypes And Migrations

### New DocTypes

- `BEDO Meeting`
- `BEDO Meeting Participant`
- `ARD Workflow Instance`
- `ARD Workflow Node State`
- `ARD Deadline Ledger`
- `ARD Deadline Pause`
- `ARD Team Member`
- `ARD Interruption Request`
- `ARD Interruption Case`
- `ARD SCMDP Submission`
- `BEDO Supplier Order`

### Extended DocTypes

- `SRS Approval`
  - Add `approval_department`.
  - Add `workflow_generation`.
  - Add optional meeting and ARD links.
- `BEDO Notification`
  - Add `source_department`, `workflow_generation`, optional `meeting`, and action validity fields.
- `BEDO Command Center Handoff`
  - Add `generation`, `meeting`, `handover_confirmation_status`, failure fields, and reset/superseded fields.
- `BEDO Deadline`
  - Add generation and reset/superseded status values where needed.
- `BEDO Supplier File`
  - Keep for compatibility; backfill to `BEDO Supplier Order` where safe.

### Migration Rules

- Migrations must be idempotent on fresh and existing sites.
- Never reset user passwords.
- Never overwrite manually changed profile data.
- Reactivate legacy ARD seed users only through safe seed/profile repair.
- Backfill existing SRS approvals to `SRS`.
- Backfill existing Command Center approvals to `Command Center`.
- Backfill existing supplier extension approvals to `Suppliers`.
- Mark stale generation records non-actionable instead of deleting audit history.

## API And Permission Matrix

All browser calls continue through:

`Browser -> Next.js BFF -> signed Frappe service API -> MariaDB/Redis`

### Backend API Families

- `meeting_service.py`
  - List visible meetings.
  - Schedule handover meeting.
  - Schedule ARD internal sync meeting.
  - Confirm lead attendance and team selection.
  - Run reminders, auto-completion, and overdue checks.
- `workflow_reset_service.py`
  - Reset Command Center.
  - Reset SRS to Action Paths.
  - Reset SRS to Coordination Meeting.
- `ard_workflow_service.py`
  - Start ARD idempotently.
  - Get ARD workspace.
  - Schedule internal sync.
  - Assign owner and team.
  - Record progress review outcome.
  - Submit interruption request.
  - Resolve interruption work.
  - Submit SCMDP.
- `supplier_order_service.py`
  - Create generic supplier orders.
  - List supplier orders by permission.
  - Mark delivered or request extension.

### Permissions

- General Manager: all approval resolution, resets, cross-department visibility, overdue notifications.
- Command Center Representative: handoff decisions, Case 3 meeting scheduling, handover confirmation, procurement confirmation, Command Center colleague selection.
- SRS Manager: required handover lead, SRS attendee selection, attendance confirmation.
- SRS Electronics Section Head: electronics interruption classification and completion only.
- ARD Manager: ARD meeting scheduling, handover confirmation as lead, owner assignment, all ARD visibility.
- ARD Project Owner: team selection, progress review outcome, interruption request, prototyping completion, SCMDP.
- ARD Section Head, Team Leader, Engineer: assigned project visibility and meeting visibility.
- User Administrator: manage new ARD and Command Center users through existing admin rules.
- System Administrator: retain technical access.

## ARD Node And Edge Definition

Lanes:

- Handover
- ARD Formation
- Review
- Interruption Paths
- Final Submission

Nodes:

- `HANDOVER_COMPLETE`
- `INTERNAL_ARD_SYNC_MEETING`
- `ARD_PROJECT_OWNER_ASSIGNMENT`
- `ARD_TEAM_SELECTION`
- `PROGRESS_REVIEW_MEETING`
- `GM_APPROVAL`
- `COMMAND_CENTER_PROCUREMENT_CONFIRMATION`
- `ELECTRONICS_SYSTEM_DESIGN`
- `CONCEPT_PROOF_PROTOTYPING`
- `SCMDP_SUBMISSION`

Primary path:

`HANDOVER_COMPLETE -> INTERNAL_ARD_SYNC_MEETING -> ARD_PROJECT_OWNER_ASSIGNMENT -> ARD_TEAM_SELECTION -> PROGRESS_REVIEW_MEETING`

On Plan path:

`PROGRESS_REVIEW_MEETING -> SCMDP_SUBMISSION`

Request Interruption path:

`PROGRESS_REVIEW_MEETING -> GM_APPROVAL -> selected interruption nodes -> SCMDP_SUBMISSION`

Unselected interruption nodes remain not applicable. Selected interruption nodes run in parallel and must all resolve before SCMDP unlocks.

## Meeting Lifecycle

Statuses:

- `DRAFT`
- `PENDING_CONFIRMATION`
- `CONFIRMED`
- `SCHEDULED`
- `COMPLETED`
- `OVERDUE`
- `CANCELLED`
- `SUPERSEDED_BY_RESET`

Rules:

- Participants are active user records only.
- Lead team selection is restricted by department server-side.
- Reminder timestamps are stored per participant or per meeting/reminder bucket to prevent duplicates.
- Meetings are scoped to source workflow generation.
- Reset supersedes meetings and suppresses reminders.
- Handover meetings use the fixed second-working-day date.
- ARD internal sync meetings can be any future date/time selected by the ARD Manager.
- Progress review meetings are auto-created from ARD team selection.

## Deadline Calculations

- Use Africa/Cairo.
- Use the existing BEDO working week and working-day calendar from `deadline_service.py`.
- ARD total active budget is seven working days.
- Milestone 1 is due by the end of working day 3.
- Milestone 2 is due by the end of working day 4.
- Whole saved days carry forward; partial hours do not.
- Paused blockers do not consume active budget.
- Blocking cases use reference-count or explicit blocker rows to avoid double pause/resume.

## Reset Boundaries

Reset Command Center:

- Preserve SRS output.
- Supersede Command Center handoff generation, meetings, reminders, approvals, supplier records in scope, and ARD generation.
- Return handoff to pending Command Center decision.

Reset SRS to Action Paths:

- Preserve SRS owner, team, coordination, deliverables, selected case, and prior gates.
- Reset selected case branch and all downstream Command Center/ARD/supplier state.
- Start a fresh deadline using the original approved duration.

Reset SRS to Coordination Meeting:

- Preserve SRS Gateway and project owner.
- Clear team, coordination, deliverables, case, approvals, deadlines, PMDP/BMDP, Command Center, suppliers, and ARD.
- Resume at Coordination Meeting.

## Approval Categorization

Categories:

- `SRS`
- `ARD`
- `Command Center`
- `Suppliers`

The backend must filter approvals by category and role. The UI tabs are presentation only and cannot be trusted for permission enforcement.

## Supplier-Order Model

`BEDO Supplier Order` is the normalized future model. Existing `BEDO Supplier File` remains compatible for current Command Center Case 2 behavior. Electronics subcases 2 and 3 create supplier orders that remain tracked after ARD completion and do not block ARD after their workflow condition is complete.

## Notification Events

New notification types cover:

- Meeting invitation and reminders.
- Attendance confirmation.
- Meeting overdue.
- ARD started, owner assigned, team assigned, interruption submitted/approved/denied.
- Procurement pending.
- Electronics action required.
- Supplier order created.
- Prototyping confirmation required.
- SCMDP submitted.
- Handover failed or forced by GM.
- Workflow reset.

Notifications must include source department, workflow generation, action route, and stale-action invalidation.

## Test Plan

Backend tests:

- ARD roles, seed users, and legacy user reactivation.
- Meeting date calculation, participant restrictions, confirmation, reminders, completion, and overdue.
- ARD start idempotency and route visibility.
- Handover success/failure and GM continue anyway.
- Reset targets and stale generation invalidation.
- ARD deadline ledger, carryover, pause/resume, blockers, and overdue notifications.
- Interruption cases, supplier order creation, SCMDP validation, and permission denials.
- HMAC service API protection.

Frontend tests:

- Sidebar bottom utility navigation and logout POST.
- Meeting cards and team selection UI.
- Command Center sub-tabs and Case 3 handover.
- Approval category tabs and richer cards.
- ARD flowchart nodes, conditional inactive states, and interruption form.
- Copy-path controls and no file browse controls.
- Notifications filters and responsive states.

## Compatibility Risks

- Frappe DocType changes must be valid on both fresh and existing MariaDB sites.
- Existing SRS behavior is high risk because much of it is centralized in `project_service.py`.
- Scheduler behavior must stay idempotent because Railway can retry or restart jobs.
- Resets can leave stale approvals or notifications actionable unless every read path checks generation.
- The real ARD section names and employee roster are not known yet.

## Assumptions

- Neutral ARD section identifiers may be used until the business provides real ARD sections.
- Development seed users use existing safe seed password behavior.
- Existing SRS flowchart visual language is the source for shared flowchart primitives.
- Railway scheduler service will run in production for meeting reminders, completion, and overdue checks.
