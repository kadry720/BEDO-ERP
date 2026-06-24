# Accessibility Report

## Improvements

- Added a portal dialog primitive with `role="dialog"` and `aria-modal="true"`.
- Added central Escape handling, Tab trapping, focus restoration, and body scroll lock.
- Electronics Cases uses semantic headings, table markup, explicit labels for selects and deadline inputs, and text status labels in addition to color.
- Sidebar route visibility for ARD Electronics Cases is role-based and does not rely on username checks.

## Automated Coverage

- `apps/web/bedo-web/tests/dialog-system.test.ts` protects the dialog primitive source contract.
- `apps/web/bedo-web/tests/electronics-cases-route.test.ts` protects role-gated navigation and route wiring.

## Remaining Manual QA

- Browser-level keyboard traversal should be rechecked against live seeded data for SRS and ARD dialogs.
- Mobile viewport checks should be repeated at 360px for long workflow forms and Electronics queue actions.
