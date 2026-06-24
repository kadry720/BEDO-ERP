# UI Refactor Baseline

- Source repository: `kadry720/BEDO-ERP`
- Fresh clone path: `C:\Users\kadoo\OneDrive\Documents\BEDO-ERP-master-frontend-ui-ux-refactor-part2`
- Authoritative source branch: `origin/codex/ard-workflow-meetings-reset-overhaul`
- Source SHA: `f91eda5ea40032c7957748863fb2f68aa1ed0d54`
- Working branch: `master-frontend-ui-ux-refactor-part2`
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

## Part 2 Addendum

- Previous UI refactor commit `afeed2172acbbf1ceea36599498900312ef5be29` was cherry-picked onto this isolated branch.
- New authorized backend work is limited to the SRS Electronics Section Head capability role and trainer-level ARD Electronics Cases queue.
- Source branch `origin/codex/ard-workflow-meetings-reset-overhaul` remains untouched.
