# UI Refactor Baseline

- Source repository: `kadry720/BEDO-ERP`
- Fresh clone path: `C:\Users\kadoo\OneDrive\Documents\BEDO-ERP-master-ui-refactor`
- Authoritative source branch: `origin/codex/ard-workflow-meetings-reset-overhaul`
- Source SHA: `f91eda5ea40032c7957748863fb2f68aa1ed0d54`
- Working branch: `codex/master-frontend-ui-ux-refactor`
- Date: `2026-06-24`

## Isolation Rules

- The existing checkout at `C:\Users\kadoo\OneDrive\Documents\BEDO ERP` is not used for implementation.
- `main` and `codex/ard-workflow-meetings-reset-overhaul` are read-only for this work.
- Backend, API, infrastructure, and deployment files remain behaviorally frozen for this branch.

## Frontend Surface

- Next app: `apps/web/bedo-web`
- Runtime UI concentration:
  - `components/Shell.tsx`
  - `components/Button.tsx`
  - `features/srs/*`
  - `features/ard/*`
  - `features/meetings/*`
  - `features/notifications/*`
  - `features/approvals/*`
  - `features/admin/*`
  - `features/auth/*`

## Risk Areas

- SRS and ARD workflow canvases currently duplicate presentation primitives.
- Dialogs use multiple ad hoc overlay shells.
- Shell navigation, utilities, session polling, conflict handling, and logout are concentrated in one large component.
- Meetings, notifications, and approvals have correct behavior but are still visually inconsistent with a unified internal tool system.
- ARD output labels require normalization without changing backend field names or payloads.
