# UI Audit

## Current State

The frontend is a compact Next.js application with most user-facing behavior in client components. The current branch already includes ARD workflow pages, meeting confirmation, notification read/unread controls, approval tabs, shell badge counts, and secure logout.

## Shared UI Gaps

- Only one global button primitive exists: `components/Button.tsx`.
- Inputs, selects, tables, badges, cards, dialogs, shell navigation, page headers, and empty/error/loading states are implemented repeatedly.
- Several modals use similar `fixed inset-0` overlays without a shared focus or keyboard behavior.
- Text sizing, spacing, shadows, and tone classes are mostly scattered Tailwind strings.

## Workflow Gaps

- SRS workflow presentation primitives live inside `features/srs/TrainerWorkspace.tsx` and `features/srs/workflowPresentation.ts`.
- ARD workflow presentation primitives live inside `features/ard/ArdWorkspace.tsx`.
- SRS and ARD share visual patterns but not reusable renderer components.
- Business definitions must stay separate: node IDs, labels, action strings, payload fields, and API endpoints are not interchangeable.

## Page-Level Gaps

- Shell needs decomposition into focused components while preserving polling, idle, conflict, attention, counts, route visibility, and logout behavior.
- Meetings should move from accordion/card grid toward agenda/detail behavior without changing confirmation payloads.
- Notifications should become a stronger inbox/list-detail surface while preserving read/unread actions and action URL normalization.
- Approvals should become a queue/detail surface while preserving POST payloads and lazy detail route compatibility.
- GM, SRS, ARD, and Command Center dashboards need clearer audience-specific status wording.

## Non-Goals

- No backend logic changes.
- No API payload changes.
- No new persistence invented in the frontend.
- No supplier center route unless an existing API contract supports it.
