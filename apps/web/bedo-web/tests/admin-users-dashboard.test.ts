import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("admin users dashboard preserves API methods and confirms delete", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "admin", "AdminUsersDashboard.tsx"), "utf-8");

  assert.match(source, /fetch\("\/api\/admin\/users"/);
  assert.match(source, /method: mode === "create" \? "POST" : "PATCH"/);
  assert.match(source, /method: "DELETE"/);
  assert.match(source, /body: JSON\.stringify\(\{ user: user\.user \}\)/);
  assert.match(source, /deleteCandidate/);
  assert.match(source, /DeleteUserConfirmModal/);
  assert.match(source, /Protected user cannot be deleted/);
});
