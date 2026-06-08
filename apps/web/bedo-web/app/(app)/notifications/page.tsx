import Link from "next/link";
import { normalizeProjectActionUrl } from "@/lib/route-ids";
import type { NotificationRow } from "@/features/srs/types";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page() {
  const session = await requireSession();
  const data = await frappeCall<{ notifications: NotificationRow[]; unread: number }>("bedo_platform.api.web.list_notifications", { limit: 50 }, session.user).catch(
    () => ({ notifications: [], unread: 0 })
  );
  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="text-xs font-bold uppercase text-muted">Notifications</div>
        <h1 className="mt-2 text-3xl font-bold text-ink">In-App Notifications</h1>
      </header>
      <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
        <div className="mb-4 text-sm font-semibold text-muted">{data.unread} unread</div>
        <div className="grid gap-3">
          {data.notifications.map((notification) => (
            <Link key={notification.name} href={notification.action_url ? normalizeProjectActionUrl(notification.action_url) : "/notifications"} className="rounded-md border border-gray-200 bg-white p-4 transition hover:border-slate-300 hover:bg-gray-50">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="font-bold text-ink">{notification.title}</div>
                <span className={`rounded-full border px-2.5 py-1 text-xs font-bold ${notification.is_read ? "border-gray-200 bg-gray-100 text-gray-600" : "border-blue-200 bg-blue-50 text-blue-800"}`}>
                  {notification.is_read ? "Read" : "Unread"}
                </span>
              </div>
              <p className="mt-2 text-sm text-muted">{notification.message}</p>
            </Link>
          ))}
          {!data.notifications.length && <div className="rounded-md border border-dashed border-gray-300 p-6 text-sm text-muted">No notifications.</div>}
        </div>
      </div>
    </section>
  );
}
