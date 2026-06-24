"use client";

import { useMemo, useState } from "react";
import { Bell, CheckCheck, ExternalLink, Search } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button, LinkButton } from "@/components/ui/Button";
import { EmptyState, Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { FieldLabel, FieldText, TextInput } from "@/components/ui/Field";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
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

type NotificationFilter = "all" | "unread" | "read";

export function NotificationsPage({ initialNotifications, initialUnread }: Props) {
  const [notifications, setNotifications] = useState(initialNotifications);
  const [unread, setUnread] = useState(initialUnread);
  const [selectedName, setSelectedName] = useState(() => initialNotifications.find((notification) => !notification.is_read)?.name || initialNotifications[0]?.name || "");
  const [updating, setUpdating] = useState("");
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<NotificationFilter>("all");

  const visibleNotifications = useMemo(() => filterNotifications(notifications, { search, filter }), [notifications, search, filter]);
  const selectedNotification = visibleNotifications.find((notification) => notification.name === selectedName) || visibleNotifications[0] || null;
  const filterOptions = useMemo(() => notificationFilterOptions(notifications), [notifications]);

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
    const nextNotifications = Array.isArray(data.notifications) ? data.notifications : [];
    setNotifications(nextNotifications);
    setUnread(Number(data.unread || 0));
    setSelectedName(notification || nextNotifications[0]?.name || "");
    window.dispatchEvent(new Event("bedo:notifications-changed"));
  }

  return (
    <section className="space-y-4">
      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <Panel>
        <PanelHeader className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-xs font-black uppercase tracking-wide text-slate-500">Inbox</div>
              <div className="mt-1 text-sm font-semibold text-slate-600">{unread} unread, {visibleNotifications.length} shown</div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <SegmentedControl label="Notification filter" options={filterOptions} value={filter} onChange={(value) => setFilter(value as NotificationFilter)} />
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={!unread || updating === "mark_all_read"}
                onClick={() => updateNotifications("mark_all_read")}
              >
                <CheckCheck className="h-4 w-4" />
                Mark all as read
              </Button>
            </div>
          </div>
          <FieldLabel>
            <FieldText>Search</FieldText>
            <span className="focus-within:focus-ring mt-2 flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3">
              <Search className="h-4 w-4 text-slate-400" />
              <TextInput className="mt-0 border-0 px-0 outline-none focus-visible:outline-transparent" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Title, message, project, trainer..." />
            </span>
          </FieldLabel>
        </PanelHeader>

        <PanelBody>
          {visibleNotifications.length ? (
            <div className="grid gap-4 xl:grid-cols-[minmax(320px,430px)_1fr]">
              <NotificationList rows={visibleNotifications} selected={selectedNotification} onSelect={setSelectedName} />
              {selectedNotification && (
                <NotificationDetail
                  notification={selectedNotification}
                  disabled={updating === selectedNotification.name}
                  updateNotifications={updateNotifications}
                />
              )}
            </div>
          ) : (
            <EmptyState title="No notifications match the current filters." description="Change search or filter settings to see more inbox items." />
          )}
        </PanelBody>
      </Panel>
    </section>
  );
}

function NotificationList({ rows, selected, onSelect }: { rows: NotificationRow[]; selected: NotificationRow | null; onSelect: (notification: string) => void }) {
  const groups = groupNotificationsByDate(rows);
  return (
    <div className="min-w-0 rounded-md border border-slate-200">
      {groups.map((group) => (
        <section key={group.label} className="border-b border-slate-200 last:border-b-0">
          <div className="bg-slate-50 px-4 py-2 text-xs font-black uppercase tracking-wide text-slate-500">{group.label}</div>
          <div className="divide-y divide-slate-100">
            {group.rows.map((notification) => {
              const active = selected?.name === notification.name;
              return (
                <button
                  key={notification.name}
                  type="button"
                  className={`focus-ring block w-full px-4 py-3 text-left transition ${active ? "bg-slate-950 text-white" : notification.is_read ? "bg-white hover:bg-slate-50" : "bg-blue-50/70 hover:bg-blue-50"}`}
                  onClick={() => onSelect(notification.name)}
                >
                  <div className="flex items-start gap-3">
                    <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${notification.is_read ? active ? "bg-slate-500" : "bg-slate-300" : "bg-blue-600"}`} />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-black">{notification.title}</div>
                      <div className={`mt-1 truncate text-xs font-semibold ${active ? "text-slate-300" : "text-slate-500"}`}>{notification.type_label || notification.notification_type}</div>
                      {(notification.project_code || notification.project_name || notification.trainer_item_name) && (
                        <div className={`mt-1 truncate text-xs font-semibold ${active ? "text-slate-300" : "text-slate-600"}`}>
                          {[notification.project_code, notification.project_name, notification.trainer_item_name].filter(Boolean).join(" | ")}
                        </div>
                      )}
                    </div>
                    <Badge tone={notification.is_read ? "slate" : "blue"}>{notification.is_read ? "Read" : "Unread"}</Badge>
                  </div>
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}

function NotificationDetail({
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
    <article className="min-w-0 rounded-md border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-md bg-slate-900 p-2 text-white">
                <Bell className="h-4 w-4" />
              </span>
              <Badge tone={notification.is_read ? "slate" : "blue"}>{notification.is_read ? "Read" : "Unread"}</Badge>
              <Badge tone="slate">{notification.priority || "Normal"}</Badge>
            </div>
            <h3 className="mt-3 break-words text-2xl font-black text-slate-950">{notification.title}</h3>
            <div className="mt-1 text-sm font-semibold text-slate-500">{notification.type_label || notification.notification_type}</div>
          </div>
        </div>
      </div>
      <div className="grid gap-4 px-5 py-5">
        {(notification.project_code || notification.project_name || notification.trainer_item_name) && (
          <div className="grid gap-3 md:grid-cols-3">
            <DetailBlock label="Project Code" value={notification.project_code || notification.project || "-"} />
            <DetailBlock label="Project Name" value={notification.project_name || "-"} />
            <DetailBlock label="Trainer Item" value={notification.trainer_item_name || notification.trainer_item || "-"} />
          </div>
        )}
        <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm font-semibold leading-6 text-slate-700">{notification.message}</div>
        <div className="flex flex-wrap items-center gap-2">
          {notification.is_read ? (
            <Button type="button" variant="secondary" size="sm" disabled={disabled} onClick={() => updateNotifications("mark_unread", notification.name)}>
              Mark as unread
            </Button>
          ) : (
            <Button type="button" variant="secondary" size="sm" disabled={disabled} onClick={() => updateNotifications("mark_read", notification.name)}>
              Mark as read
            </Button>
          )}
          {actionUrl && (
            <LinkButton href={actionUrl} size="sm">
              <ExternalLink className="h-3.5 w-3.5" />
              Open
            </LinkButton>
          )}
        </div>
      </div>
    </article>
  );
}

function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="text-[11px] font-black uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-slate-950">{value || "-"}</div>
    </div>
  );
}

function filterNotifications(rows: NotificationRow[], filters: { search: string; filter: NotificationFilter }) {
  const needle = filters.search.trim().toLowerCase();
  return rows.filter((row) => {
    if (filters.filter === "read" && !row.is_read) return false;
    if (filters.filter === "unread" && row.is_read) return false;
    if (!needle) return true;
    return [row.title, row.message, row.type_label, row.notification_type, row.project_code, row.project_name, row.trainer_item_name, row.priority]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(needle);
  });
}

function notificationFilterOptions(rows: NotificationRow[]) {
  const read = rows.filter((row) => row.is_read).length;
  const unread = rows.length - read;
  return [
    { value: "all", label: "All", count: rows.length },
    { value: "unread", label: "Unread", count: unread },
    { value: "read", label: "Read", count: read },
  ];
}

function groupNotificationsByDate(rows: NotificationRow[]) {
  const groups = new Map<string, NotificationRow[]>();
  for (const row of rows) {
    const label = dateGroupLabel(row.created_at);
    groups.set(label, [...(groups.get(label) || []), row]);
  }
  return Array.from(groups, ([label, groupedRows]) => ({ label, rows: groupedRows }));
}

function dateGroupLabel(value: string) {
  if (!value) return "Undated";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Undated";
  return date.toLocaleDateString("en-US", { dateStyle: "medium", timeZone: "Africa/Cairo" });
}
