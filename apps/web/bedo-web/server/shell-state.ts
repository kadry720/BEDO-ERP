import type { NotificationRow } from "@/features/srs/types";
import { frappeCall } from "@/server/frappe";

type NotificationSummary = {
  unread?: number;
  notifications?: NotificationRow[];
};

type ApprovalCount = {
  count?: number;
};

type MeetingSummary = {
  count?: number;
};

type ShellStateDependencies = {
  listNotifications: (user: string) => Promise<NotificationSummary>;
  getPendingApprovalCount: (user: string) => Promise<ApprovalCount>;
  listPendingMeetings: (user: string) => Promise<MeetingSummary>;
};

export type ShellState = {
  unreadNotifications: number;
  pendingApprovals: number;
  pendingMeetings: number;
  total: number;
  notifications: NotificationRow[];
};

const defaultDependencies: ShellStateDependencies = {
  listNotifications: (user) => frappeCall<NotificationSummary>("bedo_platform.api.web.list_notifications", { limit: 25 }, user),
  getPendingApprovalCount: (user) => frappeCall<ApprovalCount>("bedo_platform.api.web.get_pending_approval_count", {}, user),
  listPendingMeetings: (user) => frappeCall<MeetingSummary>("bedo_platform.api.web.list_my_meetings", { status: "PENDING_CONFIRMATION" }, user),
};

export async function loadShellState(user: string, dependencies: ShellStateDependencies = defaultDependencies): Promise<ShellState> {
  const [notifications, approvals, meetings] = await Promise.all([
    dependencies.listNotifications(user).catch((): NotificationSummary => ({ unread: 0, notifications: [] })),
    dependencies.getPendingApprovalCount(user).catch((): ApprovalCount => ({ count: 0 })),
    dependencies.listPendingMeetings(user).catch((): MeetingSummary => ({ count: 0 })),
  ]);
  const rows = Array.isArray(notifications.notifications) ? notifications.notifications : [];
  const unreadNotifications = Number(notifications.unread ?? rows.filter((notification) => !notification.is_read).length);
  const pendingApprovals = Number(approvals.count || 0);
  const pendingMeetings = Number(meetings.count || 0);
  return {
    unreadNotifications,
    pendingApprovals,
    pendingMeetings,
    total: unreadNotifications + pendingApprovals + pendingMeetings,
    notifications: rows,
  };
}
