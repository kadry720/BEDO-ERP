"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType, ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bell,
  BellRing,
  ClipboardCheck,
  LayoutDashboard,
  LogOut,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Shield,
  UserCircle,
  Users,
} from "lucide-react";
import { normalizeProjectActionUrl } from "@/lib/route-ids";
import { displayName, isAdminUser, routeLabels, type BedoUserContext } from "@/lib/routes";
import type { NotificationRow } from "@/features/srs/types";

type NavItem = {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
};

export function Shell({ session, children }: { session: BedoUserContext; children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const navItems = useMemo(() => phaseNavItems(session), [session]);
  const pageTitle = pageTitleFor(pathname, navItems);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden border-r border-slate-800 bg-slate-950 text-slate-100 shadow-xl transition-[width] duration-200 lg:block ${
          collapsed ? "w-20" : "w-72"
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4">
          <Link href={session.landing_route || "/gm"} className="min-w-0">
            <div className={`text-base font-black tracking-wide text-white ${collapsed ? "text-center" : ""}`}>BEDO</div>
            {!collapsed && <div className="mt-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">Industrial Process Governance</div>}
          </Link>
          <button
            type="button"
            className="focus-ring rounded-md p-2 text-slate-400 hover:bg-slate-900 hover:text-white"
            onClick={() => setCollapsed((value) => !value)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </button>
        </div>
        <nav className="space-y-1 px-3 py-5">
          {navItems.map((item) => (
            <SidebarNavItem key={item.href} item={item} active={isActive(pathname, item.href)} collapsed={collapsed} />
          ))}
        </nav>
      </aside>

      <div className={`transition-[padding] duration-200 ${collapsed ? "lg:pl-20" : "lg:pl-72"}`}>
        <TopBar session={session} pageTitle={pageTitle} />
        <main className="px-4 py-5 md:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

function phaseNavItems(session: BedoUserContext): NavItem[] {
  const allowed = new Set(session.modules.map((module) => module.route));
  const items: NavItem[] = [];
  if (allowed.has("/gm")) items.push({ href: "/gm", label: "GM Support Office Dashboard", icon: LayoutDashboard });
  if (allowed.has("/srs")) items.push({ href: "/srs", label: "SRS Dashboard", icon: ClipboardCheck });
  if (isAdminUser(session)) items.push({ href: "/admin/users", label: "Admin Dashboard", icon: Users });
  return items;
}

function SidebarNavItem({ item, active, collapsed }: { item: NavItem; active: boolean; collapsed: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      title={collapsed ? item.label : undefined}
      className={`group flex min-h-11 items-center gap-3 rounded-md px-3 text-sm font-semibold transition ${
        active ? "bg-amber-500 text-slate-950 shadow-sm" : "text-slate-300 hover:bg-slate-900 hover:text-white"
      } ${collapsed ? "justify-center" : ""}`}
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </Link>
  );
}

function TopBar({ session, pageTitle }: { session: BedoUserContext; pageTitle: string }) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 shadow-sm backdrop-blur md:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <Menu className="h-5 w-5 text-slate-400 lg:hidden" />
        <div className="min-w-0">
          <h1 className="truncate text-lg font-black text-slate-950">{pageTitle}</h1>
          <p className="hidden text-xs font-medium text-slate-500 sm:block">BEDO enterprise workspace</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <NotificationBell />
        <ApprovalIcon />
        <UserMenu session={session} />
      </div>
    </header>
  );
}

function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<{ notifications: NotificationRow[]; unread: number }>({ notifications: [], unread: 0 });
  const panelRef = useRef<HTMLDivElement>(null);

  async function load() {
    const response = await fetch("/api/notifications");
    if (response.ok) setData(await response.json());
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    function onClick(event: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  async function markRead(notification?: string) {
    const response = await fetch("/api/notifications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(notification ? { notification } : {}),
    });
    if (response.ok) setData(await response.json());
  }

  return (
    <div ref={panelRef} className="relative">
      <button
        type="button"
        className="focus-ring relative rounded-md border border-slate-200 bg-white p-2 text-slate-700 hover:bg-slate-50"
        onClick={() => {
          setOpen((value) => !value);
          void load();
        }}
        title="Notifications"
      >
        {data.unread ? <BellRing className="h-5 w-5" /> : <Bell className="h-5 w-5" />}
        {data.unread > 0 && <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-red-600 px-1.5 py-0.5 text-[10px] font-bold text-white">{data.unread}</span>}
      </button>
      {open && <NotificationPanel data={data} markRead={markRead} />}
    </div>
  );
}

function NotificationPanel({ data, markRead }: { data: { notifications: NotificationRow[]; unread: number }; markRead: (notification?: string) => void }) {
  const unread = data.notifications.filter((item) => !item.is_read);
  const earlier = data.notifications.filter((item) => item.is_read);
  return (
    <div className="absolute right-0 top-12 z-50 w-[min(430px,calc(100vw-2rem))] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <div className="text-sm font-black text-slate-950">Notifications</div>
          <div className="text-xs font-medium text-slate-500">{data.unread} unread</div>
        </div>
        <button className="rounded-md px-2 py-1 text-xs font-bold text-slate-600 hover:bg-slate-100" type="button" onClick={() => markRead()}>
          Mark all read
        </button>
      </div>
      <div className="max-h-[70vh] overflow-y-auto p-3">
        <NotificationSection title="Unread" rows={unread} markRead={markRead} />
        <NotificationSection title="Earlier" rows={earlier} markRead={markRead} />
        {!data.notifications.length && (
          <div className="rounded-md border border-dashed border-slate-300 px-4 py-8 text-center text-sm font-semibold text-slate-500">No notifications.</div>
        )}
      </div>
    </div>
  );
}

function NotificationSection({ title, rows, markRead }: { title: string; rows: NotificationRow[]; markRead: (notification?: string) => void }) {
  if (!rows.length) return null;
  return (
    <section className="mb-3 last:mb-0">
      <div className="mb-2 px-1 text-[11px] font-black uppercase tracking-wide text-slate-500">{title}</div>
      <div className="grid gap-2">
        {rows.map((row) => (
          <NotificationRowItem key={row.name} row={row} markRead={markRead} />
        ))}
      </div>
    </section>
  );
}

function NotificationRowItem({ row, markRead }: { row: NotificationRow; markRead: (notification?: string) => void }) {
  return (
    <div className={`rounded-md border p-3 ${row.is_read ? "border-slate-200 bg-white" : "border-blue-200 bg-blue-50/70"}`}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-md bg-slate-900 p-2 text-white">
          <Bell className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="truncate text-sm font-black text-slate-950">{row.title || row.type_label}</div>
              <div className="mt-0.5 text-xs font-semibold text-slate-500">{row.type_label}</div>
            </div>
            {!row.is_read && <span className="mt-1 h-2 w-2 rounded-full bg-blue-600" />}
          </div>
          {(row.project_name || row.trainer_item_name) && (
            <div className="mt-2 truncate text-xs font-semibold text-slate-700">
              {[row.project_code, row.project_name, row.trainer_item_name].filter(Boolean).join(" | ")}
            </div>
          )}
          <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-600">{row.message}</p>
          <div className="mt-3 flex items-center justify-between gap-3">
            <span className="text-[11px] font-medium text-slate-500">{formatDate(row.created_at)}</span>
            <div className="flex items-center gap-2">
              {!row.is_read && (
                <button className="rounded-md px-2 py-1 text-xs font-bold text-slate-600 hover:bg-white" type="button" onClick={() => markRead(row.name)}>
                  Mark read
                </button>
              )}
              {row.action_url && (
                <Link className="rounded-md bg-slate-900 px-2 py-1 text-xs font-bold text-white hover:bg-slate-700" href={normalizeProjectActionUrl(row.action_url)}>
                  Open
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ApprovalIcon() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    fetch("/api/approvals?count=1")
      .then((response) => response.json())
      .then((data) => setCount(Number(data.count || 0)))
      .catch(() => setCount(0));
  }, []);
  return (
    <Link href="/approvals" className="focus-ring relative rounded-md border border-slate-200 bg-white p-2 text-slate-700 hover:bg-slate-50" title="Approvals">
      <ClipboardCheck className="h-5 w-5" />
      {count > 0 && <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-amber-500 px-1.5 py-0.5 text-[10px] font-black text-slate-950">{count}</span>}
    </Link>
  );
}

function UserMenu({ session }: { session: BedoUserContext }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-2 py-1.5">
      <Link href="/profile" className="hidden items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-950 sm:flex">
        <UserCircle className="h-4 w-4" />
        <span className="max-w-40 truncate">{displayName(session)}</span>
      </Link>
      {isAdminUser(session) && <Shield className="h-4 w-4 text-amber-600" />}
      <form action="/api/auth/logout" method="post">
        <button className="focus-ring rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-950" title="Log out" type="submit">
          <LogOut className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}

function pageTitleFor(pathname: string, navItems: NavItem[]) {
  const matched = navItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`));
  if (matched) return matched.label;
  if (pathname.startsWith("/approvals")) return "Approvals";
  if (pathname.startsWith("/profile")) return "My Profile";
  return routeLabels[pathname] || "BEDO Workspace";
}

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function formatDate(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
