import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("sidebar bottom contains labeled utility links and logout form", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "components", "Shell.tsx"), "utf-8");

  assert.match(source, /SidebarUtilityNav/);
  assert.match(source, /href="\/meetings"/);
  assert.match(source, /label="Meetings"/);
  assert.match(source, /href="\/notifications"/);
  assert.match(source, /label="Notifications"/);
  assert.match(source, /href="\/approvals"/);
  assert.match(source, /label="Approvals"/);
  assert.match(source, /action="\/api\/auth\/logout"/);
  assert.match(source, />Log out</);
});

test("top bar no longer renders duplicate utility controls", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "components", "Shell.tsx"), "utf-8");
  const topBarStart = source.indexOf("function TopBar(");
  const topBarEnd = source.indexOf("function NotificationBell(");
  const topBarSource = source.slice(topBarStart, topBarEnd);

  assert.doesNotMatch(topBarSource, /NotificationBell/);
  assert.doesNotMatch(topBarSource, /ApprovalIcon/);
  assert.doesNotMatch(topBarSource, /UserMenu/);
});
