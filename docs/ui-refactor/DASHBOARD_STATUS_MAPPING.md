# Dashboard Status Mapping

## GM

- The GM dashboard does not treat SRS completion as total project completion.
- When all downstream proof is unavailable, the UI uses in-progress or unavailable wording rather than declaring overall completion.
- Protected by `apps/web/bedo-web/tests/dashboard-lifecycle-wording.test.ts`.

## SRS

- SRS dashboard remains scoped to SRS-visible projects, trainer states, owners, teams, deadlines, approvals, blockers, and SRS completion.

## ARD

- ARD dashboard and ARD project detail remain scoped to ARD-visible workflows and trainer items.
- ARD Manager sees all active ARD workflows; ARD employees see assigned trainer workflows only.

## Electronics Cases

- `/srs/ard-electronics-cases` is not a project-card dashboard. It is a trainer-level queue for active ARD Electronics interruption node states.
