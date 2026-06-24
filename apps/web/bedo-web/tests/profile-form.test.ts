import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("profile form preserves PATCH endpoint and exposes account UX controls", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "auth", "ProfileForm.tsx"), "utf-8");

  assert.match(source, /fetch\("\/api\/profile"/);
  assert.match(source, /method: "PATCH"/);
  assert.match(source, /\.\.\.formState/);
  assert.match(source, /\.\.\.passwordState/);
  assert.match(source, /Unsaved changes/);
  assert.match(source, /Show \$\{label\}/);
  assert.match(source, /Hide \$\{label\}/);
});
