import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("workflow reset BFF route uses signed Frappe reset method", () => {
  const route = join(import.meta.dirname, "..", "app", "api", "workflow-resets", "route.ts");

  assert.equal(existsSync(route), true);
  assert.match(readFileSync(route, "utf-8"), /bedo_platform\.api\.web\.execute_workflow_reset/);
});

test("handover failure approvals expose continue and command center reset actions", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "approvals", "ApprovalsPage.tsx"), "utf-8");

  assert.match(source, /HANDOVER_FAILURE_GM_APPROVAL/);
  assert.match(source, /Continue Anyway/);
  assert.match(source, /Reset Command Center/);
  assert.match(source, /reset_command_center/);
});
