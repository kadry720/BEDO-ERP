import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("GM dashboard does not present SRS completion as whole-project completion", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "srs", "ProjectDashboard.tsx"), "utf-8");

  assert.doesNotMatch(source, /Project completion is calculated from SRS-completed trainer items/);
  assert.match(source, /SRS completion is shown as evidence, not final project completion/);
  assert.match(source, /Lifecycle Complete Projects/);
  assert.match(source, /const done = isGm \? \[\] : buckets\.filter/);
});
