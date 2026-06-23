import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("approval center groups pending approvals by department source", () => {
  const pageSource = readFileSync(join(import.meta.dirname, "..", "features", "approvals", "ApprovalsPage.tsx"), "utf-8");
  const typeSource = readFileSync(join(import.meta.dirname, "..", "features", "srs", "types.ts"), "utf-8");

  assert.match(typeSource, /approval_department: string/);
  assert.match(pageSource, /approvalDepartmentOrder = \["SRS", "ARD", "Command Center", "Suppliers"\]/);
  assert.match(pageSource, /role="tablist"/);
  assert.match(pageSource, /aria-label="Approval source"/);
  assert.match(pageSource, /departmentFilter/);
  assert.match(pageSource, /approval\.approval_department/);
  assert.doesNotMatch(pageSource, /Approval Center/);
});
