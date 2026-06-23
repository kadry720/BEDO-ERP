import assert from "node:assert/strict";
import test from "node:test";
import { loadShellState } from "../server/shell-state";

test("shell state combines notification and approval badge data in one call", async () => {
  const state = await loadShellState("gm@example.local", {
    listNotifications: async () => ({
      notifications: [
        notificationRow("n1", 0),
        notificationRow("n2", 1),
      ],
    }),
    getPendingApprovalCount: async () => ({ count: 3 }),
    listPendingMeetings: async () => ({ count: 2, meetings: [] }),
  });

  assert.equal(state.unreadNotifications, 1);
  assert.equal(state.pendingApprovals, 3);
  assert.equal(state.pendingMeetings, 2);
  assert.equal(state.total, 6);
  assert.equal(state.notifications.length, 2);
});

test("shell state keeps the page usable when one backend badge source fails", async () => {
  const state = await loadShellState("gm@example.local", {
    listNotifications: async () => {
      throw new Error("notifications unavailable");
    },
    getPendingApprovalCount: async () => ({ count: 2 }),
    listPendingMeetings: async () => {
      throw new Error("meetings unavailable");
    },
  });

  assert.equal(state.unreadNotifications, 0);
  assert.equal(state.pendingApprovals, 2);
  assert.equal(state.pendingMeetings, 0);
  assert.equal(state.total, 2);
  assert.deepEqual(state.notifications, []);
});

function notificationRow(name: string, is_read: number) {
  return {
    name,
    notification_type: "INFO",
    title: "Notice",
    message: "Message",
    action_url: "",
    priority: "Normal",
    is_read,
    created_at: "2026-06-21 10:00:00",
  };
}
