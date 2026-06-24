# Flowchart Parity Report

## Shared Presentation Architecture

- SRS and ARD now render through `apps/web/bedo-web/components/workflow/WorkflowCanvas.tsx`.
- Both workflows use `WorkflowActionDialog` for node actions and `WorkflowOutputSummary` for completed-node output.
- Geometry, lanes, connector routes, node icons, subtitles, availability checks, action forms, and payload mappings remain supplied by the owning SRS/ARD feature modules.

## Preserved Contracts

- SRS node IDs, connector routes, never-open node IDs, action strings, API URLs, and payload keys are protected by `apps/web/bedo-web/tests/ui-contract-baseline.test.ts`.
- ARD node IDs, connector routes, action strings, interruption payload keys, and workflow API route behavior are protected by the same baseline test and ARD-specific tests.
- The shared renderer does not change workflow transitions, permissions, clickability, deadlines, or response handling.

## Visual Parity

- Both canvases use the same shell structure: workflow header, stat strip, legend, lane rail, scaled grid, SVG connectors, node cards, active deadline badge, and modal shell.
- ARD keeps ARD-specific node labels, connection routes, case sections, SCMDP output, and interruption actions.
- SRS keeps SRS-specific tabs, command-center handoff, supplier tab, node actions, and never-open display nodes.

## Cleanup

- Legacy local `FlowNode`, header-stat, edge-path, and duplicate modal-shell code was removed from SRS and ARD workflow files.
- Dead shell popover/user-menu UI was removed only after confirming it had no live references.

