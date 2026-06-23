import { NotificationsPage } from "@/features/notifications/NotificationsPage";
import type { NotificationRow } from "@/features/srs/types";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page() {
  const session = await requireSession();
  const data = await frappeCall<{ notifications: NotificationRow[]; unread: number }>("bedo_platform.api.web.list_notifications", { limit: 50 }, session.user).catch(
    () => ({ notifications: [], unread: 0 })
  );
  return <NotificationsPage initialNotifications={data.notifications} initialUnread={data.unread} />;
}
