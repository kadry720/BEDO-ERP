import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("sidebar bottom contains labeled utility links and logout form", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "components", "Shell.tsx"), "utf-8");

  assert.match(source, /SidebarUtilityNav/);
  assert.match(source, /href="\/meetings"/);
  assert.match(source, /label="Meetings"/);
  assert.match(source, /label="Meetings"[^>]+badge=\{shellState\.pendingMeetings\}/s);
  assert.match(source, /href="\/notifications"/);
  assert.match(source, /label="Notifications"/);
  assert.match(source, /href="\/approvals"/);
  assert.match(source, /label="Approvals"/);
  assert.match(source, /action="\/api\/auth\/logout"/);
  assert.match(source, />Log out</);
  assert.doesNotMatch(source, /ArrowLeft/);
  assert.doesNotMatch(source, /aria-label="Back"/);
  assert.doesNotMatch(source, />Back</);
});

test("top bar no longer renders duplicate utility controls", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "components", "Shell.tsx"), "utf-8");
  const topBarStart = source.indexOf("function TopBar(");
  const topBarEnd = source.indexOf("function pageTitleFor(");
  const topBarSource = source.slice(topBarStart, topBarEnd);

  assert.doesNotMatch(topBarSource, /NotificationBell/);
  assert.doesNotMatch(topBarSource, /ApprovalIcon/);
  assert.doesNotMatch(topBarSource, /UserMenu/);
});

test("mobile menu opens a full navigation drawer and legacy shell popovers are removed", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "components", "Shell.tsx"), "utf-8");

  assert.match(source, /MobileNavigationDrawer/);
  assert.match(source, /aria-label="Open navigation"/);
  assert.match(source, /role="dialog"/);
  assert.match(source, /aria-modal="true"/);
  assert.match(source, /Dashboards/);
  assert.match(source, /Work Queue/);
  assert.match(source, /href="\/profile"/);
  assert.doesNotMatch(source, /function NotificationBell/);
  assert.doesNotMatch(source, /function ApprovalIcon/);
  assert.doesNotMatch(source, /function UserMenu/);
});
