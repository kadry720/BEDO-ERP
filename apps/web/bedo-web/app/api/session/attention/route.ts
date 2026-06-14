import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

type NotificationSummary = {
  unread?: number;
  notifications?: Array<{ is_read?: number }>;
};

type ApprovalCount = {
  count?: number;
};

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const [notifications, approvals] = await Promise.all([
    frappeCall<NotificationSummary>("bedo_platform.api.web.list_notifications", {}, session.user).catch(
      (): NotificationSummary => ({ unread: 0, notifications: [] })
    ),
    frappeCall<ApprovalCount>("bedo_platform.api.web.get_pending_approval_count", {}, session.user).catch(
      (): ApprovalCount => ({ count: 0 })
    ),
  ]);
  const unreadNotifications = Number(
    notifications.unread ?? notifications.notifications?.filter((notification) => !notification.is_read).length ?? 0
  );
  const pendingApprovals = Number(approvals.count || 0);
  return NextResponse.json({
    unreadNotifications,
    pendingApprovals,
    total: unreadNotifications + pendingApprovals,
  });
}
