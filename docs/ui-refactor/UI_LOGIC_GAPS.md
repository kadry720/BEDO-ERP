# UI Logic Gaps

This file records UX outcomes that require backend data or contracts not currently exposed by the source branch. No fake data or invented frontend state was added for these gaps.

## GM Whole-Lifecycle Completion

- Gap: the project dashboard response exposes generic trainer counts but does not prove that every required active department workflow is complete.
- UI behavior: GM no longer treats SRS-completed trainer counts as final project completion. Projects remain in lifecycle progress unless completion can be proven by existing response data.
- Needed contract: a portfolio aggregate that reports required departmental workflows and final lifecycle completion per trainer/project.

## Cross-Project Supplier Center

- Gap: the branch has supplier-file actions and supplier-related workflow data, but no complete list/API contract for a standalone cross-project supplier center.
- UI behavior: existing supplier surfaces remain tied to the trainer/workflow context. No global supplier route was invented.
- Needed contract: supplier list endpoint, access rules, filter fields, and detail/action payloads.

## Profile Avatar Image

- Gap: session/profile data does not provide an avatar image URL.
- UI behavior: profile uses generated initials only.
- Needed contract: trusted avatar URL or file reference if real images are required.

## Executive Department Timeline

- Gap: GM dashboard data does not expose a full cross-department timeline for every project.
- UI behavior: displays conservative project evidence and does not fabricate missing stages.
- Needed contract: per-project department stage summary with SRS, Command Center, ARD, supplier, and final completion status.

