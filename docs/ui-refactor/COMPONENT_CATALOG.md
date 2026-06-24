# Component Catalog

## Core

- `Button`, `IconButton`, `LinkButton`: source-owned button family.
- `Badge`: compact badge primitive.
- `Panel`: bordered surface primitive.
- `Field`: label, hint, and error wrapper.

## Navigation

- `SegmentedControl`: accessible tab/filter control used by meetings and notifications.

## Dialog

- `Dialog`: permanent portal-based dialog primitive.
  - Renders through `createPortal(..., document.body)`.
  - Locks body scroll while mounted.
  - Restores focus to the previous element.
  - Handles Escape and Tab focus trapping.
  - Supports size variants, header, context summary, body scroll, and footer.
- `WorkflowActionDialog`: shared SRS/ARD workflow action shell built on `Dialog`.

## Workflow

- `WorkflowCanvas`: shared SRS/ARD flowchart renderer preserving workflow-specific nodes, positions, connectors, and availability.
- `WorkflowOutputSummary`: shared output de-duplication and semantic display.

## Data Display

- Existing source-owned tables remain feature-local. The Electronics Cases page introduces a compact trainer-level queue table using the shared button and status styling.
