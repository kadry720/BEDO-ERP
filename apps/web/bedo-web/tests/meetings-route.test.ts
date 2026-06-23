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

test("meeting cards expose details and attendance confirmation controls", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "meetings", "MeetingsPage.tsx"), "utf-8");

  assert.match(source, /openMeeting/);
  assert.match(source, /Confirm attendance/);
  assert.match(source, /confirmation_candidates/);
  assert.match(source, /api\/meetings\/\$\{routeSegment\(meeting\.name\)\}\/confirm/);
});
