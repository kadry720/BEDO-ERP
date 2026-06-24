# Dependency Decision

## Decision

Do not add a new UI component library or workflow/canvas dependency at the start of this refactor.

## Rationale

- The app already depends on React, Next, Tailwind, `clsx`, and `lucide-react`.
- The SRS and ARD canvases have fixed domain-specific geometry and connectors; a general graph library would add bundle weight and increase migration risk.
- The prompt requires preserving exact node IDs, geometry, connector routes, action strings, and payload keys. Extracting internal shared primitives is lower risk than replacing the renderer.
- Accessibility improvements can be implemented with small local primitives before evaluating a headless-dialog dependency.

## Allowed Revisit Criteria

A dependency can be reconsidered only if a documented gap remains after local primitives are extracted, and only if it does not alter backend contracts or workflow semantics.
