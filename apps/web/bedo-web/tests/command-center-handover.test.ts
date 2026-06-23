import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("command center case 3 handover BFF routes are wired to signed Frappe methods", () => {
  const handoffMeetingRoute = join(import.meta.dirname, "..", "app", "api", "command-center", "handoffs", "[trainerItemId]", "case-3-meeting", "route.ts");
  const handoffConfirmationRoute = join(import.meta.dirname, "..", "app", "api", "command-center", "handoffs", "[trainerItemId]", "handover-confirmation", "route.ts");
  const meetingConfirmationRoute = join(import.meta.dirname, "..", "app", "api", "meetings", "[meetingId]", "confirm", "route.ts");

  assert.equal(existsSync(handoffMeetingRoute), true);
  assert.equal(existsSync(handoffConfirmationRoute), true);
  assert.equal(existsSync(meetingConfirmationRoute), true);
  assert.match(readFileSync(handoffMeetingRoute, "utf-8"), /bedo_platform\.api\.web\.schedule_case3_handover_meeting/);
  assert.match(readFileSync(handoffConfirmationRoute, "utf-8"), /bedo_platform\.api\.web\.submit_case3_handover_confirmation/);
  assert.match(readFileSync(meetingConfirmationRoute, "utf-8"), /bedo_platform\.api\.web\.confirm_case3_handover_meeting/);
});

test("command center workspace uses reusable sub-tabs and shows case 3 handover actions", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "srs", "TrainerWorkspace.tsx"), "utf-8");

  assert.match(source, /commandCenterSubTabs/);
  assert.match(source, /SRS → ARD/);
  assert.match(source, /Handover Meeting/);
  assert.match(source, /Handover Confirmation/);
  assert.match(source, /case-3-meeting/);
  assert.match(source, /handover-confirmation/);
});
