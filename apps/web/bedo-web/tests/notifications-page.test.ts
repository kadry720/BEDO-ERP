import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("notifications page delegates read and unread actions to a client page", () => {
  const appPage = join(import.meta.dirname, "..", "app", "(app)", "notifications", "page.tsx");
  const clientPage = join(import.meta.dirname, "..", "features", "notifications", "NotificationsPage.tsx");

  assert.equal(existsSync(appPage), true);
  assert.equal(existsSync(clientPage), true);
  const appSource = readFileSync(appPage, "utf-8");
  const clientSource = readFileSync(clientPage, "utf-8");

  assert.match(appSource, /<NotificationsPage/);
  assert.doesNotMatch(appSource, /In-App Notifications/);
  assert.match(clientSource, /Mark all as read/);
  assert.match(clientSource, /Mark as read/);
  assert.match(clientSource, /Mark as unread/);
  assert.match(clientSource, /"mark_unread"/);
});

test("notifications API supports read, unread, and mark-all-read actions", () => {
  const route = readFileSync(join(import.meta.dirname, "..", "app", "api", "notifications", "route.ts"), "utf-8");

  assert.match(route, /mark_notification_as_read/);
  assert.match(route, /mark_notification_as_unread/);
  assert.match(route, /mark_all_notifications_as_read/);
});
