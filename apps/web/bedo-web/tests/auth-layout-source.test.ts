import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("authenticated layout uses the signed session without a per-navigation Frappe me call", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "app", "(app)", "layout.tsx"), "utf-8");

  assert.doesNotMatch(source, /bedo_platform\.api\.web\.me/);
});
