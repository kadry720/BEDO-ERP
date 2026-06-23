"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ComponentType, ReactNode } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bell,
  BellRing,
  CalendarClock,
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
import { shellPollIntervals, shouldPollShellWhenVisible } from "@/lib/shell-polling";
import type { NotificationRow } from "@/features/srs/types";
import type { ShellState } from "@/server/shell-state";

type NavItem = {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
};

const approvalNotificationTypes = new Set(["GM_APPROVAL_REQUIRED", "SRS_MANAGER_APPROVAL_REQUIRED", "GM_APPROVAL_COMPLETED"]);
const idleTimeoutMs = 30 * 60 * 1000;
const reminderDelayMs = 10 * 60 * 1000;
const emptyShellState: ShellState = {
  unreadNotifications: 0,
  pendingApprovals: 0,
  pendingMeetings: 0,
  total: 0,
  notifications: [],
};

export function Shell({ session, children }: { session: BedoUserContext; children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [shellState, setShellState] = useState<ShellState>(emptyShellState);
  const navItems = useMemo(() => phaseNavItems(session), [session]);
  const pageTitle = pageTitleFor(pathname, navItems);

  const refreshShellState = useCallback(async () => {
    try {
      const response = await fetch("/api/session/shell-state");
      if (!response.ok) return null;
      const nextState = (await response.json()) as ShellState;
      setShellState(nextState);
      return nextState;
    } catch {
      return null;
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <SessionLifecycle
        session={session}
        loadShellState={refreshShellState}
      />
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-slate-800 bg-slate-950 text-slate-100 shadow-xl transition-[width] duration-200 lg:flex ${
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
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
          {navItems.map((item) => (
            <SidebarNavItem key={item.href} item={item} active={isActive(pathname, item.href)} collapsed={collapsed} />
          ))}
        </nav>
        <SidebarUtilityNav session={session} collapsed={collapsed} shellState={shellState} refreshShellState={refreshShellState} />
      </aside>

      <div className={`transition-[padding] duration-200 ${collapsed ? "lg:pl-20" : "lg:pl-72"}`}>
        <TopBar pageTitle={pageTitle} />
        <main className="px-4 pb-24 pt-5 md:px-6 lg:px-8 lg:pb-5">{children}</main>
        <MobileUtilityBar session={session} shellState={shellState} refreshShellState={refreshShellState} />
      </div>
    </div>
  );
}

type AttentionSummary = {
  unreadNotifications: number;
  pendingApprovals: number;
  pendingMeetings: number;
  total: number;
};

function SessionLifecycle({
  session,
  loadShellState,
}: {
  session: BedoUserContext;
  loadShellState: () => Promise<ShellState | null>;
}) {
  const router = useRouter();
  const [attention, setAttention] = useState<AttentionSummary | null>(null);
  const [attentionOpen, setAttentionOpen] = useState(false);
  const [loginChallengeId, setLoginChallengeId] = useState("");
  const idleTimerRef = useRef<number | null>(null);
  const reminderTimerRef = useRef<number | null>(null);
  const sessionKey = session.session_id || session.user;
  const suppressKey = `bedo_attention_suppress:${sessionKey}`;
  const reminderKey = `bedo_attention_next:${sessionKey}`;

  async function logoutWithReason(reason: string) {
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => null);
    window.location.assign(`/login?error=${encodeURIComponent(reason)}`);
  }

  function shouldShowAttention(summary: AttentionSummary) {
    if (!summary.total) return false;
    if (window.sessionStorage.getItem(suppressKey) === "1") return false;
    const nextReminderAt = Number(window.sessionStorage.getItem(reminderKey) || 0);
    return !nextReminderAt || Date.now() >= nextReminderAt;
  }

  async function loadAttention() {
    const summary = await loadShellState();
    if (!summary) return;
    setAttention(summary);
    if (shouldShowAttention(summary)) setAttentionOpen(true);
  }

  function scheduleReminderCheck() {
    if (reminderTimerRef.current) window.clearTimeout(reminderTimerRef.current);
    const nextReminderAt = Number(window.sessionStorage.getItem(reminderKey) || 0);
    if (!nextReminderAt) return;
    const delay = Math.max(0, nextReminderAt - Date.now());
    reminderTimerRef.current = window.setTimeout(() => {
      window.sessionStorage.removeItem(reminderKey);
      void loadAttention();
    }, delay);
  }

  function remindLater() {
    window.sessionStorage.setItem(reminderKey, String(Date.now() + reminderDelayMs));
    setAttentionOpen(false);
    scheduleReminderCheck();
  }

  function viewAttention() {
    window.sessionStorage.setItem(suppressKey, "1");
    window.sessionStorage.removeItem(reminderKey);
    setAttentionOpen(false);
    if ((attention?.pendingApprovals || 0) > 0) {
      router.push("/approvals");
      return;
    }
    if ((attention?.pendingMeetings || 0) > 0) {
      router.push("/meetings");
      return;
    }
    router.push("/notifications");
  }

  function resetIdleTimer() {
    if (idleTimerRef.current) window.clearTimeout(idleTimerRef.current);
    idleTimerRef.current = window.setTimeout(() => {
      void logoutWithReason("timeout");
    }, idleTimeoutMs);
  }

  useEffect(() => {
    void loadAttention();
    scheduleReminderCheck();

    const activityEvents = ["mousemove", "mousedown", "keydown", "scroll", "touchstart"];
    activityEvents.forEach((eventName) => window.addEventListener(eventName, resetIdleTimer, { passive: true }));
    resetIdleTimer();

    const checkSessionStatus = async () => {
      if (!shouldPollShellWhenVisible(document.visibilityState)) return;
      const response = await fetch("/api/session/status");
      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.valid === false) {
        await logoutWithReason("session_replaced");
        return;
      }
      if (data.conflict?.challengeId) setLoginChallengeId(String(data.conflict.challengeId));
    };

    const statusInterval = window.setInterval(checkSessionStatus, shellPollIntervals.sessionStatusMs);

    const attentionInterval = window.setInterval(() => {
      if (!shouldPollShellWhenVisible(document.visibilityState)) return;
      void loadAttention();
    }, shellPollIntervals.shellStateMs);

    function handleVisibilityChange() {
      if (!shouldPollShellWhenVisible(document.visibilityState)) return;
      void checkSessionStatus();
      void loadAttention();
    }
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      activityEvents.forEach((eventName) => window.removeEventListener(eventName, resetIdleTimer));
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (idleTimerRef.current) window.clearTimeout(idleTimerRef.current);
      if (reminderTimerRef.current) window.clearTimeout(reminderTimerRef.current);
      window.clearInterval(statusInterval);
      window.clearInterval(attentionInterval);
    };
  }, [sessionKey, loadShellState]);

  async function respondToLoginChallenge(action: "allow" | "deny") {
    if (!loginChallengeId) return;
    const response = await fetch("/api/session/conflict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ challengeId: loginChallengeId, action }),
    });
    if (!response.ok) {
      setLoginChallengeId("");
      return;
    }
    if (action === "allow") {
      await logoutWithReason("session_transferred");
      return;
    }
    setLoginChallengeId("");
  }

  return (
    <>
      {attentionOpen && attention && (
        <AttentionModal summary={attention} onRemindLater={remindLater} onView={viewAttention} />
      )}
      {loginChallengeId && (
        <SessionConflictModal
          onAllow={() => respondToLoginChallenge("allow")}
          onDeny={() => respondToLoginChallenge("deny")}
        />
      )}
    </>
  );
}

function AttentionModal({
  summary,
  onRemindLater,
  onView,
}: {
  summary: AttentionSummary;
  onRemindLater: () => void;
  onView: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/55 p-4">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-amber-100 p-2 text-amber-700">
            <BellRing className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-black text-slate-950">Items need your attention</h2>
            <p className="mt-2 text-sm font-medium leading-6 text-slate-600">
              You have {summary.unreadNotifications} unread notification(s), {summary.pendingApprovals} pending approval(s), and {summary.pendingMeetings} pending meeting(s).
            </p>
          </div>
        </div>
        <div className="mt-6 grid gap-2 sm:grid-cols-2">
          <button
            className="focus-ring rounded-md border border-slate-300 bg-white px-4 py-3 text-sm font-black text-slate-700 hover:bg-slate-50"
            type="button"
            onClick={onRemindLater}
          >
            Remind me later
          </button>
          <button
            className="focus-ring rounded-md bg-slate-900 px-4 py-3 text-sm font-black text-white hover:bg-slate-700"
            type="button"
            onClick={onView}
          >
            View
          </button>
        </div>
      </div>
    </div>
  );
}

function SessionConflictModal({ onAllow, onDeny }: { onAllow: () => void; onDeny: () => void }) {
  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/65 p-4">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-red-100 p-2 text-red-700">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-black text-slate-950">Another device is trying to sign in</h2>
            <p className="mt-2 text-sm font-medium leading-6 text-slate-600">
              Allowing this login will sign you out here and transfer the account to the other device. Denying it keeps this session active.
            </p>
          </div>
        </div>
        <div className="mt-6 grid gap-2 sm:grid-cols-2">
          <button
            className="focus-ring rounded-md border border-slate-300 bg-white px-4 py-3 text-sm font-black text-slate-700 hover:bg-slate-50"
            type="button"
            onClick={onDeny}
          >
            Deny
          </button>
          <button
            className="focus-ring rounded-md bg-slate-900 px-4 py-3 text-sm font-black text-white hover:bg-slate-700"
            type="button"
            onClick={onAllow}
          >
            Allow
          </button>
        </div>
      </div>
    </div>
  );
}

function phaseNavItems(session: BedoUserContext): NavItem[] {
  const allowed = new Set(session.modules.map((module) => module.route));
  const items: NavItem[] = [];
  if (allowed.has("/gm")) items.push({ href: "/gm", label: "GM Support Office Dashboard", icon: LayoutDashboard });
  if (allowed.has("/srs")) items.push({ href: "/srs", label: "SRS Dashboard", icon: ClipboardCheck });
  if (allowed.has("/ard")) items.push({ href: "/ard", label: "ARD Dashboard", icon: ClipboardCheck });
  if (allowed.has("/command-center")) items.push({ href: "/command-center", label: "Command Center Dashboard", icon: ClipboardCheck });
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

function SidebarUtilityNav({
  session,
  collapsed,
  shellState,
  refreshShellState,
}: {
  session: BedoUserContext;
  collapsed: boolean;
  shellState: ShellState;
  refreshShellState: () => Promise<ShellState | null>;
}) {
  useEffect(() => {
    function refreshCount() {
      void refreshShellState();
    }
    window.addEventListener("bedo:approvals-changed", refreshCount);
    window.addEventListener("bedo:notifications-changed", refreshCount);
    window.addEventListener("bedo:meetings-changed", refreshCount);
    return () => {
      window.removeEventListener("bedo:approvals-changed", refreshCount);
      window.removeEventListener("bedo:notifications-changed", refreshCount);
      window.removeEventListener("bedo:meetings-changed", refreshCount);
    };
  }, [refreshShellState]);

  return (
    <div className="border-t border-slate-800 px-3 py-4">
      <div className="space-y-1">
        <SidebarUtilityLink href="/meetings" label="Meetings" icon={CalendarClock} collapsed={collapsed} badge={shellState.pendingMeetings} />
        <SidebarUtilityLink href="/notifications" label="Notifications" icon={Bell} collapsed={collapsed} badge={shellState.unreadNotifications} />
        <SidebarUtilityLink href="/approvals" label="Approvals" icon={ClipboardCheck} collapsed={collapsed} badge={shellState.pendingApprovals} />
      </div>
      <Link
        href="/profile"
        title={collapsed ? displayName(session) : undefined}
        className={`mt-4 flex min-h-12 items-center gap-3 rounded-md border border-slate-800 px-3 py-2 text-sm font-bold text-slate-200 hover:bg-slate-900 hover:text-white ${
          collapsed ? "justify-center" : ""
        }`}
      >
        <ProfileAvatar session={session} />
        {!collapsed && <span className="min-w-0 truncate">{displayName(session)}</span>}
      </Link>
      <form action="/api/auth/logout" method="post" className="mt-3">
        <button
          className={`focus-ring flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-red-600 px-3 text-sm font-black text-white hover:bg-red-700 ${
            collapsed ? "px-2" : ""
          }`}
          title="Log out"
          type="submit"
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Log out</span>}
        </button>
      </form>
    </div>
  );
}

function SidebarUtilityLink({
  href,
  label,
  icon: Icon,
  collapsed,
  badge = 0,
}: {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  collapsed: boolean;
  badge?: number;
}) {
  return (
    <Link
      href={href}
      title={collapsed ? label : undefined}
      className={`relative flex min-h-10 items-center gap-3 rounded-md px-3 text-sm font-semibold text-slate-300 hover:bg-slate-900 hover:text-white ${
        collapsed ? "justify-center" : ""
      }`}
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
      {badge > 0 && <span className="ml-auto min-w-5 rounded-full bg-amber-500 px-1.5 py-0.5 text-center text-[10px] font-black text-slate-950">{badge}</span>}
    </Link>
  );
}

function ProfileAvatar({ session }: { session: BedoUserContext }) {
  const initials = [session.first_name, session.last_name]
    .filter(Boolean)
    .map((part) => part.slice(0, 1).toUpperCase())
    .join("")
    .slice(0, 2) || session.username.slice(0, 2).toUpperCase();
  return <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-800 text-xs font-black text-white">{initials}</span>;
}

function MobileUtilityBar({
  session,
  shellState,
  refreshShellState,
}: {
  session: BedoUserContext;
  shellState: ShellState;
  refreshShellState: () => Promise<ShellState | null>;
}) {
  useEffect(() => {
    function refreshCount() {
      void refreshShellState();
    }
    window.addEventListener("bedo:approvals-changed", refreshCount);
    window.addEventListener("bedo:notifications-changed", refreshCount);
    window.addEventListener("bedo:meetings-changed", refreshCount);
    return () => {
      window.removeEventListener("bedo:approvals-changed", refreshCount);
      window.removeEventListener("bedo:notifications-changed", refreshCount);
      window.removeEventListener("bedo:meetings-changed", refreshCount);
    };
  }, [refreshShellState]);

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-slate-200 bg-white px-2 py-2 shadow-2xl lg:hidden">
      <MobileUtilityLink href="/meetings" label="Meetings" icon={CalendarClock} badge={shellState.pendingMeetings} />
      <MobileUtilityLink href="/notifications" label="Notifications" icon={Bell} badge={shellState.unreadNotifications} />
      <MobileUtilityLink href="/approvals" label="Approvals" icon={ClipboardCheck} badge={shellState.pendingApprovals} />
      <MobileUtilityLink href="/profile" label="Profile" icon={UserCircle} />
      <form action="/api/auth/logout" method="post" className="flex justify-center">
        <button className="focus-ring flex min-h-12 min-w-12 flex-col items-center justify-center gap-1 rounded-md px-2 text-[10px] font-black text-red-600" type="submit">
          <LogOut className="h-5 w-5" />
          <span>Log out</span>
        </button>
      </form>
      <span className="sr-only">{displayName(session)}</span>
    </nav>
  );
}

function MobileUtilityLink({
  href,
  label,
  icon: Icon,
  badge = 0,
}: {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  badge?: number;
}) {
  return (
    <Link href={href} className="relative flex min-h-12 flex-col items-center justify-center gap-1 rounded-md px-2 text-[10px] font-black text-slate-700">
      <Icon className="h-5 w-5" />
      <span>{label}</span>
      {badge > 0 && <span className="absolute right-2 top-1 min-w-4 rounded-full bg-amber-500 px-1 text-[9px] font-black text-slate-950">{badge}</span>}
    </Link>
  );
}

function TopBar({ pageTitle }: { pageTitle: string }) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 shadow-sm backdrop-blur md:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <Menu className="h-5 w-5 text-slate-400 lg:hidden" />
        <div className="min-w-0">
          <h1 className="truncate text-lg font-black text-slate-950">{pageTitle}</h1>
          <p className="hidden text-xs font-medium text-slate-500 sm:block">BEDO enterprise workspace</p>
        </div>
      </div>
    </header>
  );
}

function NotificationBell({
  openSignal,
  shellState,
  refreshShellState,
}: {
  openSignal: number;
  shellState: ShellState;
  refreshShellState: () => Promise<ShellState | null>;
}) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<{ notifications: NotificationRow[]; unread: number }>(() => notificationDataFromShellState(shellState));
  const panelRef = useRef<HTMLDivElement>(null);

  async function load() {
    const response = await fetch("/api/notifications");
    if (response.ok) setData(await response.json());
  }

  useEffect(() => {
    setData(notificationDataFromShellState(shellState));
  }, [shellState]);

  useEffect(() => {
    if (!openSignal) return;
    setOpen(true);
    void load();
  }, [openSignal]);

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
    if (response.ok) {
      setData(await response.json());
      void refreshShellState();
    }
  }

  return (
    <div ref={panelRef} className="relative">
      <button
        type="button"
        className="focus-ring relative rounded-md border border-slate-200 bg-white p-2 text-slate-700 hover:bg-slate-50"
        onClick={() => {
          setOpen((value) => {
            const nextOpen = !value;
            if (nextOpen) void load();
            return nextOpen;
          });
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

function notificationDataFromShellState(shellState: ShellState) {
  return {
    notifications: shellState.notifications,
    unread: shellState.unreadNotifications,
  };
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
  const actionUrl = notificationActionUrl(row);
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
              {actionUrl && (
                <Link className="rounded-md bg-slate-900 px-2 py-1 text-xs font-bold text-white hover:bg-slate-700" href={actionUrl}>
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

function notificationActionUrl(row: NotificationRow) {
  if (approvalNotificationTypes.has(row.notification_type)) return "/approvals";
  if (!row.action_url) return "";
  return normalizeProjectActionUrl(row.action_url);
}

function ApprovalIcon({ count, refreshShellState }: { count: number; refreshShellState: () => Promise<ShellState | null> }) {
  useEffect(() => {
    function refreshCount() {
      void refreshShellState();
    }
    window.addEventListener("bedo:approvals-changed", refreshCount);
    return () => {
      window.removeEventListener("bedo:approvals-changed", refreshCount);
    };
  }, [refreshShellState]);

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
  if (pathname.startsWith("/meetings")) return "Meetings";
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
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short", timeZone: "Africa/Cairo" });
}
