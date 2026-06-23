# Meetings And Workflow Reset Architecture

## Current-State Findings

- The application already has scheduled Frappe jobs for deadline overdue checks.
- There is no reusable meeting model yet.
- Command Center handoff records are active/inactive, but they do not have a generation field.
- SRS approvals do not have a department category or generation field.
- Notifications link directly to action URLs and need stale-action invalidation for reset safety.

## Meeting Data Model

### `BEDO Meeting`

Fields:

- `meeting_id`
- `meeting_type`
- `project`
- `trainer_item`
- `source_workflow`
- `source_workflow_generation`
- `source_node`
- `organizer`
- `organizer_department`
- `scheduled_at`
- `time_zone`
- `expected_end_at`
- `status`
- `title`
- `description`
- `created_at`
- `confirmed_at`
- `completed_at`
- `overdue_at`
- `one_day_reminder_sent_at`
- `one_hour_reminder_sent_at`
- `related_reference_doctype`
- `related_reference_name`
- `is_superseded`
- `superseded_by_reset`

### `BEDO Meeting Participant`

Fields:

- `meeting`
- `user`
- `department`
- `participation_source`
- `selected_by`
- `is_required`
- `confirmation_status`
- `confirmed_at`
- `is_active`
- `superseded_by_reset`

## Lifecycle

1. Create meeting in `PENDING_CONFIRMATION` or `SCHEDULED`.
2. Add organizer and automatic required leads.
3. Leads select department attendees and confirm attendance.
4. Meeting card stays visible with team/date context.
5. Scheduler sends one-day and one-hour reminders once.
6. Scheduler auto-completes eligible meetings.
7. Scheduler marks meetings overdue when action is missing after expected end.
8. Reset marks meetings `SUPERSEDED_BY_RESET` and prevents future reminders/actions.

## Handover Meeting Rules

- Applies only to Command Center Case 3.
- Date is exactly the second working date after the server timestamp when Case 3 enters handover-meeting stage.
- Command Center may choose time only on that date.
- Required leads are SRS Manager and ARD Manager.
- Command Center organizer selects active Command Center colleagues.
- SRS Manager selects active SRS attendees.
- ARD Manager selects active ARD attendees.
- Each lead confirms attendance after team selection.

## ARD Internal Meeting Rules

- ARD Manager schedules any future date/time.
- ARD Manager selects active ARD participants.
- Meeting auto-completes one hour after scheduled start.
- Completion unlocks ARD project owner assignment.

## Progress Review Meeting Rules

- Auto-created after ARD team selection.
- Scheduled at 09:00 on the next working morning after two complete working days.
- Includes ARD Manager, ARD project owner, and selected ARD team members.
- Auto-completes one hour after scheduled start.
- Progress Review node then waits for owner outcome.

## Scheduler Design

Frappe scheduler jobs:

- `meeting_service.run_meeting_reminders`
- `meeting_service.run_meeting_auto_completion`
- `meeting_service.run_meeting_overdue_check`

Idempotency:

- Reminder timestamps are checked before notification creation.
- Completion checks current status and generation.
- Overdue checks current status, expected end, and generation.
- Reset/superseded meetings are ignored.

## Reset Architecture

The reset engine is a service boundary:

- `workflow_reset_service.reset_command_center`
- `workflow_reset_service.reset_srs_to_action_paths`
- `workflow_reset_service.reset_srs_to_coordination`

Every reset:

- Requires General Manager role.
- Runs inside a database transaction.
- Locks active trainer item, SRS workflow, Command Center handoff, and ARD workflow rows where available.
- Increments or creates a generation boundary.
- Supersedes downstream operational records.
- Leaves security audit records intact.
- Returns a fresh workspace snapshot.

## Generation Scope

Records that must carry generation:

- Command Center handoff.
- Meetings and participants.
- SRS approvals.
- ARD workflow instances and node states.
- Deadlines.
- Supplier orders.
- Notifications/action links.

Reads and mutations must reject stale generation values.

## Reset Targets

### Reset Command Center

Preserves SRS output and returns Command Center to pending decision. Supersedes Case 3 meeting, handover confirmation, handover failure approval, Command Center deadlines, supplier tasks, and ARD generation.

### Reset SRS To Action Paths

Preserves SRS work through Action Paths and selected case. Clears the selected case branch and downstream Command Center/ARD/supplier state. Starts a fresh deadline with the original approved duration.

### Reset SRS To Coordination Meeting

Preserves SRS Gateway and project owner. Clears team, coordination result, deliverables, case, approvals, PMDP/BMDP, deadlines after Gateway, Command Center, suppliers, and ARD. Resumes at Coordination Meeting.

## Audit Events

Audit records are append-only and include:

- Actor.
- Reset target.
- Project.
- Trainer item.
- Source workflow generation.
- New workflow generation.
- Source state summary.
- Reason.

Meeting events include scheduling, participant added, confirmation, completion, overdue, reminder, cancellation, and superseded by reset.

## API Matrix

- `/api/meetings`: list visible meetings.
- `/api/meetings/[meetingId]/participants`: select participants.
- `/api/meetings/[meetingId]/confirm`: confirm attendance.
- `/api/command-center/handoffs/[trainerItemId]/case-3-meeting`: schedule handover meeting.
- `/api/command-center/handoffs/[trainerItemId]/handover-confirmation`: submit successful/failed handover.
- `/api/workflow-resets`: execute supported GM reset.

All routes call signed Frappe methods and pass the authenticated Next session user.

## Compatibility Risks

- Existing notifications may need backfill to stay visible but non-actionable when stale.
- Existing approvals lack categories; backfill must infer from approval type.
- Existing Command Center handoffs lack generation; migration should default generation to `1`.
- Scheduler must run exactly as an idempotent process because multiple instances or retries may occur.

## Assumptions

- Standard meeting duration is one hour.
- Africa/Cairo is the authoritative time zone.
- Reset reasons are captured as text and may be optional unless the UI marks them required for a specific target.
