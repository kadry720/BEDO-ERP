import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("ARD flowchart BFF route uses signed Frappe flowchart method", () => {
  const route = join(import.meta.dirname, "..", "app", "api", "ard", "flowchart", "route.ts");

  assert.equal(existsSync(route), true);
  assert.match(readFileSync(route, "utf-8"), /bedo_platform\.api\.web\.get_ard_flowchart_definition/);
});
