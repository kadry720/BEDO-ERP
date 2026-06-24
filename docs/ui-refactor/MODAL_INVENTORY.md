# Modal Inventory

## Current Dialog-Like Surfaces

- `components/Shell.tsx`
  - Attention reminder dialog.
  - Session conflict dialog.
  - Notification popover/panel.
  - User menu.
- `features/srs/TrainerWorkspace.tsx`
  - SRS workflow node action/output dialog.
  - Supplier extension dialog.
- `features/ard/ArdWorkspace.tsx`
  - ARD workflow node action/output dialog.
- `features/srs/ProjectDashboard.tsx`
  - Edit project dialog.
  - Confirmation dialog.
- `features/srs/AddProjectPage.tsx`
  - Trainer item edit dialog.
  - Separation-mode choice dialog.
- `features/approvals/ApprovalsPage.tsx`
  - Approve-with-edits dialog.

## Required Refactor Direction

- Introduce shared dialog primitives under `apps/web/bedo-web/components/ui`.
- Preserve existing open/close/action behavior and payloads.
- Add consistent `role="dialog"`, `aria-modal="true"`, close labels, escape handling, focus restoration, and footer/action placement where dialogs remain.
- Do not convert backend-confirmed flows into fake frontend-only state.
