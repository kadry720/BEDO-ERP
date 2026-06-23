"use client";

import Link from "next/link";
import { Bell, CheckCheck, ExternalLink } from "lucide-react";
import { useMemo, useState } from "react";
import type { NotificationRow } from "@/features/srs/types";
import { normalizeProjectActionUrl } from "@/lib/route-ids";

type Props = {
  initialNotifications: NotificationRow[];
  initialUnread: number;
};

type NotificationPayload = {
  notifications: NotificationRow[];
  unread: number;
};

export function NotificationsPage({ initialNotifications, initialUnread }: Props) {
  const [notifications, setNotifications] = useState(initialNotifications);
  const [unread, setUnread] = useState(initialUnread);
  const [updating, setUpdating] = useState("");
  const [error, setError] = useState("");
  const grouped = useMemo(
    () => ({
      unread: notifications.filter((notification) => !notification.is_read),
      read: notifications.filter((notification) => notification.is_read),
    }),
    [notifications]
  );

  async function updateNotifications(action: "mark_read" | "mark_unread" | "mark_all_read", notification?: string) {
    setUpdating(notification || action);
    setError("");
    const response = await fetch("/api/notifications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, notification }),
    });
    const data = (await response.json().catch(() => ({}))) as Partial<NotificationPayload> & { error?: string };
    setUpdating("");
    if (!response.ok) {
      setError(data.error || "Notification could not be updated.");
      return;
    }
    setNotifications(Array.isArray(data.notifications) ? data.notifications : []);
    setUnread(Number(data.unread || 0));
    window.dispatchEvent(new Event("bedo:notifications-changed"));
  }

  return (
    <section className="space-y-4">
      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}
      <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm font-semibold text-muted">{unread} unread</div>
          <button
            type="button"
            className="focus-ring inline-flex min-h-9 items-center gap-2 rounded-md border border-slate-300 bg-white px-3 text-sm font-black text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={!unread || updating === "mark_all_read"}
            onClick={() => updateNotifications("mark_all_read")}
          >
            <CheckCheck className="h-4 w-4" />
            Mark all as read
          </button>
        </div>

        <div className="grid gap-5">
          <NotificationSection
            title="Unread"
            rows={grouped.unread}
            updating={updating}
            updateNotifications={updateNotifications}
          />
          <NotificationSection
            title="Read"
            rows={grouped.read}
            updating={updating}
            updateNotifications={updateNotifications}
          />
          {!notifications.length && <div className="rounded-md border border-dashed border-gray-300 p-6 text-sm text-muted">No notifications.</div>}
        </div>
      </div>
    </section>
  );
}

function NotificationSection({
  title,
  rows,
  updating,
  updateNotifications,
}: {
  title: string;
  rows: NotificationRow[];
  updating: string;
  updateNotifications: (action: "mark_read" | "mark_unread" | "mark_all_read", notification?: string) => Promise<void>;
}) {
  if (!rows.length) return null;
  return (
    <section>
      <div className="mb-2 text-xs font-black uppercase tracking-wide text-slate-500">{title}</div>
      <div className="grid gap-3">
        {rows.map((notification) => (
          <NotificationCard
            key={notification.name}
            notification={notification}
            disabled={updating === notification.name}
            updateNotifications={updateNotifications}
          />
        ))}
      </div>
    </section>
  );
}

function NotificationCard({
  notification,
  disabled,
  updateNotifications,
}: {
  notification: NotificationRow;
  disabled: boolean;
  updateNotifications: (action: "mark_read" | "mark_unread" | "mark_all_read", notification?: string) => Promise<void>;
}) {
  const actionUrl = notification.action_url ? normalizeProjectActionUrl(notification.action_url) : "";
  return (
    <article className={`rounded-md border p-4 ${notification.is_read ? "border-gray-200 bg-white" : "border-blue-200 bg-blue-50/70"}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 gap-3">
          <div className="mt-0.5 rounded-md bg-slate-900 p-2 text-white">
            <Bell className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="font-bold text-ink">{notification.title}</div>
            <div className="mt-1 text-xs font-semibold text-muted">{notification.type_label || notification.notification_type}</div>
          </div>
        </div>
        <span className={`rounded-full border px-2.5 py-1 text-xs font-bold ${notification.is_read ? "border-gray-200 bg-gray-100 text-gray-600" : "border-blue-200 bg-blue-50 text-blue-800"}`}>
          {notification.is_read ? "Read" : "Unread"}
        </span>
      </div>

      {(notification.project_code || notification.project_name || notification.trainer_item_name) && (
        <div className="mt-3 text-sm font-semibold text-slate-700">
          {[notification.project_code, notification.project_name, notification.trainer_item_name].filter(Boolean).join(" | ")}
        </div>
      )}
      <p className="mt-2 text-sm text-muted">{notification.message}</p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {notification.is_read ? (
          <button
            type="button"
            className="focus-ring rounded-md border border-slate-300 px-3 py-2 text-xs font-black text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={disabled}
            onClick={() => updateNotifications("mark_unread", notification.name)}
          >
            Mark as unread
          </button>
        ) : (
          <button
            type="button"
            className="focus-ring rounded-md border border-slate-300 px-3 py-2 text-xs font-black text-slate-700 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
            disabled={disabled}
            onClick={() => updateNotifications("mark_read", notification.name)}
          >
            Mark as read
          </button>
        )}
        {actionUrl && (
          <Link className="focus-ring inline-flex items-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-xs font-black text-white hover:bg-slate-700" href={actionUrl}>
            <ExternalLink className="h-3.5 w-3.5" />
            Open
          </Link>
        )}
      </div>
    </article>
  );
}
