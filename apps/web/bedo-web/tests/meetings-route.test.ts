import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("meetings app route and BFF route are wired through signed Frappe API", () => {
  const appPage = join(import.meta.dirname, "..", "app", "(app)", "meetings", "page.tsx");
  const apiRoute = join(import.meta.dirname, "..", "app", "api", "meetings", "route.ts");

  assert.equal(existsSync(appPage), true);
  assert.equal(existsSync(apiRoute), true);
  assert.match(readFileSync(apiRoute, "utf-8"), /bedo_platform\.api\.web\.list_my_meetings/);
});
