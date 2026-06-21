import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("authenticated layout refreshes user context only for legacy sessions without modules", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "app", "(app)", "layout.tsx"), "utf-8");

  assert.match(source, /session\.modules\.length/);
  assert.match(source, /bedo_platform\.api\.web\.me/);
});
