# ARD Deadline Model

## Current-State Findings

- The existing SRS deadline service supports Cairo working days, working hours, reminders, overdue checks, and simple extensions.
- ARD cannot safely reuse only `BEDO Deadline` because ARD has a seven-working-day active budget, whole-day carryover, pause/resume, and overlapping blockers.
- ARD needs an auditable ledger to avoid double-counting paused time and to explain overdue behavior.

## Time Rules

- Time zone: Africa/Cairo.
- Working week: use the existing BEDO calendar in `deadline_service.py`.
- Working hours: use the existing `WORK_START` and `WORK_END`.
- Formal counters start at 09:00 on the next working day after a partial-day completion.
- Partial remaining hours are usable for work but not credited as saved full days.

## Budget Rules

- Total ARD active budget: seven working days.
- Milestone 1 due: end of working day 3.
- Milestone 2 due: end of working day 4.
- Final due: end of remaining active budget.
- Whole saved days carry forward.
- Partial saved hours are discarded.
- Paused time does not consume budget.

## Proposed DocTypes

### `ARD Deadline Ledger`

Fields:

- `ard_workflow`
- `project`
- `trainer_item`
- `generation`
- `budget_started_at`
- `current_milestone`
- `milestone_started_at`
- `milestone_due_at`
- `final_due_at`
- `total_budget_days`
- `milestone_1_budget_days`
- `milestone_2_budget_days`
- `remaining_budget_days`
- `whole_days_consumed`
- `whole_days_saved`
- `total_paused_seconds`
- `active_blocker_count`
- `is_paused`
- `paused_started_at`
- `overdue_notified_at`
- `status`

### `ARD Deadline Pause`

Fields:

- `ledger`
- `ard_workflow`
- `interruption_case`
- `blocker_key`
- `started_at`
- `ended_at`
- `paused_seconds`
- `status`

## Milestone Mapping

Milestone 1:

- `HANDOVER_COMPLETE`
- `INTERNAL_ARD_SYNC_MEETING`
- `ARD_PROJECT_OWNER_ASSIGNMENT`
- `ARD_TEAM_SELECTION`

Milestone 2:

- `PROGRESS_REVIEW_MEETING`
- Progress review outcome.

Final:

- Approved interruption operational work where selected.
- `SCMDP_SUBMISSION`

## Pause/Resume Rules

- Approved Procurement Pause creates one blocker.
- Electronics New Design creates one blocker after classification.
- Concept-Proof Prototyping creates one blocker after approval.
- Electronics Inventory Stock and Design Complete / No Inventory are non-pausing.
- The timer is paused when `active_blocker_count > 0`.
- A blocker can start only once.
- A blocker can end only once.
- The timer resumes only when the active blocker count reaches zero.
- Completing one blocker while others remain active must not alter the due timestamp twice.

## Overdue Rules

- Paused ledgers are not marked overdue.
- Active ledgers compare current Cairo time to the current milestone due time or final due time.
- Overdue notification is sent once per relevant overdue state.
- Recipients are ARD Manager, GM, and the responsible owner where available.
- Overdue state appears on the matching ARD node.

## API Behavior

Mutations that advance ARD state must:

- Load the active ARD workflow generation.
- Validate current node state.
- Validate role and department.
- Update node state and ledger in one transaction.
- Return a fresh ARD workspace.
- Reject stale generation actions.

## Test Plan

- Working-day arithmetic for Milestone 1, Milestone 2, and final due.
- Team Selection due by working day 3.
- Progress Review due by working day 4.
- Seven-day total budget.
- Whole-day carryover.
- Partial-day discard.
- Pause start/end idempotency.
- Overlapping blockers.
- No overdue while paused.
- One overdue notification per overdue state.

## Compatibility Risks

- Existing `BEDO Deadline` jobs should not accidentally process ARD ledger rows unless explicitly adapted.
- If Railway scheduler is not running, reminders/completions/overdue checks will not fire.
- Any reset must supersede the active ledger and pauses before creating a fresh generation.

## Assumptions

- The existing BEDO working calendar remains authoritative.
- Deadline mode remains compatible with local minute-based tests, but production ARD behavior is working-day based.
- Whole-day calculations use working-day boundaries, not 24-hour elapsed windows.
