# Modal Defect Baseline

## Observed Risk

Before the reusable dialog primitive, workflow dialogs used feature-local `fixed inset-0` shells. Those shells were mounted inside feature trees that also contain large flowchart canvases and transformed/scrolling ancestors, which made z-index, focus restoration, body scroll, and pointer behavior inconsistent.

## Defect Checks

- Dialog can be opened: covered by workflow action tests and manual branch history.
- Inputs can receive focus: new `Dialog` traps focus and starts focus inside the portal.
- Text/select/checkbox controls are not covered by an overlay: portal panel is rendered above the overlay and outside transformed ancestors.
- Dialog body can scroll: `Dialog` uses `max-h-[92vh]` and `overflow-y-auto`.
- Footer actions remain reachable: `Dialog` has a fixed footer slot outside the scroll body.
- Escape closes dialog: handled centrally.
- Focus returns to trigger: previous focused element is restored on unmount.
- Background scroll is locked: `document.body.style.overflow = "hidden"`.

## Root Cause

The root presentation-layer cause was duplicated modal shells rendered in feature-local DOM trees rather than one portal-based primitive. The fix is `components/ui/Dialog.tsx` and migration of workflow/admin/approval dialogs to that primitive.
