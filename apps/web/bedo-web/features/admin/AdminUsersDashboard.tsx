"use client";

import { useEffect, useMemo, useState } from "react";
import { Edit3, Save, Search, ShieldCheck, Trash2, X } from "lucide-react";
import { Button } from "@/components/Button";
import type { AdminBootstrap, AdminUser, SecurityEvent } from "@/features/admin/types";

const hiddenAdminTableUsers = new Set(["administrator", "guest", "systemadmin", "useradmin", "securityauditor", "globalviewer"]);

function isHiddenAdminTableUser(user: AdminUser) {
  return [user.user, user.username, user.email]
    .filter(Boolean)
    .some((value) => {
      const normalized = value.toLowerCase();
      return hiddenAdminTableUsers.has(normalized) || hiddenAdminTableUsers.has(normalized.split("@")[0]);
    });
}

type UserFormMode = "create" | "edit";

type SecurityFilterState = {
  date_from: string;
  date_to: string;
  search: string;
  event_type: string;
  actor: string;
  target_user: string;
  status: string;
};

const emptySecurityFilters: SecurityFilterState = {
  date_from: "",
  date_to: "",
  search: "",
  event_type: "",
  actor: "",
  target_user: "",
  status: ""
};

export function AdminUsersDashboard({ bootstrap, securityEvents }: { bootstrap: AdminBootstrap; securityEvents: SecurityEvent[] }) {
  const canManageUsers = bootstrap.can_manage_users !== false;
  const tabs = useMemo(() => (canManageUsers ? ["Users", "Security Logs"] : ["Security Logs"]), [canManageUsers]);
  const [activeTab, setActiveTab] = useState(tabs[0]);
  const [users, setUsers] = useState(bootstrap.users);
  const [query, setQuery] = useState("");
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [deleteCandidate, setDeleteCandidate] = useState<AdminUser | null>(null);
  const [adminError, setAdminError] = useState("");
  const [adminSuccess, setAdminSuccess] = useState("");

  const filtered = useMemo(() => {
    const needle = query.toLowerCase().trim();
    const visibleUsers = users.filter((user) => !isHiddenAdminTableUser(user));
    if (!needle) return visibleUsers;
    return visibleUsers.filter((user) =>
      [user.username, user.first_name, user.last_name, user.email, user.primary_department, user.roles.join(" ")]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    );
  }, [query, users]);

  useEffect(() => {
    if (!tabs.includes(activeTab)) setActiveTab(tabs[0]);
  }, [activeTab, tabs]);

  async function submitUser(payload: Record<string, FormDataEntryValue | FormDataEntryValue[]>, mode: UserFormMode, targetUser?: string) {
    setAdminError("");
    setAdminSuccess("");
    const response = await fetch("/api/admin/users", {
      method: mode === "create" ? "POST" : "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mode === "edit" ? { ...payload, user: targetUser } : payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      setAdminError(data?.error || "User could not be saved.");
      return;
    }
    if (response.ok) {
      setUsers(data.users);
      setEditingUser(null);
      setAdminSuccess(mode === "create" ? "User created." : "User updated.");
    }
  }

  async function deleteUser(user: AdminUser) {
    setAdminError("");
    setAdminSuccess("");
    const response = await fetch("/api/admin/users", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: user.user })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      setAdminError(data?.error || "User could not be deleted.");
      return;
    }
    if (response.ok) {
      setUsers(data.users);
      if (editingUser?.user === user.user) setEditingUser(null);
      setDeleteCandidate(null);
      setAdminSuccess("User deleted.");
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="text-xs font-semibold uppercase text-muted">Administration</div>
        <h1 className="mt-2 text-3xl font-bold text-ink">{canManageUsers ? "User Administration" : "Security Logs"}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
          {canManageUsers
            ? "Manage BEDO accounts, explicit admin access, route visibility, technical Desk access, and security review."
            : "Review authentication, access-control, project, approval, and user-management events."}
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`focus-ring rounded-md px-4 py-2 text-sm font-semibold ${
              activeTab === tab ? "bg-ink text-white" : "border border-gray-300 bg-white text-gray-700"
            }`}
            type="button"
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {adminSuccess && <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm font-bold text-green-800">{adminSuccess}</div>}
      {adminError && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-800">{adminError}</div>}

      {canManageUsers && activeTab === "Users" && (
        <div className="grid gap-6 xl:grid-cols-[minmax(360px,440px)_1fr]">
          <UserForm
            bootstrap={bootstrap}
            mode={editingUser ? "edit" : "create"}
            user={editingUser}
            onCancel={() => setEditingUser(null)}
            onSubmit={submitUser}
          />

          <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-bold text-ink">Users</h2>
                <p className="text-sm text-muted">{filtered.length} active BEDO accounts</p>
              </div>
              <label className="relative block w-full md:w-96">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted" />
                <input
                  className="focus-ring w-full rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm"
                  placeholder="Search users, roles, departments"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </label>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-gray-200 text-xs uppercase text-muted">
                  <tr>
                    <th className="py-3 pr-4">User</th>
                    <th className="py-3 pr-4">Department</th>
                    <th className="py-3 pr-4">Roles</th>
                    <th className="py-3 pr-4">Status</th>
                    <th className="py-3 pr-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filtered.map((user) => (
                    <tr key={user.user}>
                      <td className="py-4 pr-4">
                        <div className="font-semibold text-ink">
                          {user.first_name} {user.last_name}
                        </div>
                        <div className="text-muted">
                          {user.username} - {user.email}
                        </div>
                        <div className="text-xs text-muted">{user.phone_number}</div>
                      </td>
                      <td className="py-4 pr-4">{user.primary_department || "Platform"}</td>
                      <td className="py-4 pr-4">
                        <div className="flex max-w-3xl flex-wrap gap-1">
                          {user.roles.map((role) => (
                            <span key={role} className="rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-700">
                              {role}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-4 pr-4">
                        <span className={`rounded px-2 py-1 text-xs font-semibold ${user.enabled ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                          {user.enabled ? "Enabled" : "Disabled"}
                        </span>
                      </td>
                      <td className="py-4 pr-4">
                        <div className="flex justify-end gap-2">
                          <IconButton label="Edit user" onClick={() => setEditingUser(user)}>
                            <Edit3 className="h-4 w-4" />
                          </IconButton>
                          <IconButton label={user.can_delete ? "Delete user" : "Protected user cannot be deleted"} disabled={!user.can_delete} onClick={() => setDeleteCandidate(user)}>
                            <Trash2 className="h-4 w-4" />
                          </IconButton>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === "Security Logs" && <SecurityLogs initialEvents={securityEvents} />}
      {deleteCandidate && (
        <DeleteUserConfirmModal
          user={deleteCandidate}
          onClose={() => setDeleteCandidate(null)}
          onConfirm={() => deleteUser(deleteCandidate)}
        />
      )}
    </section>
  );
}

function UserForm({
  bootstrap,
  mode,
  user,
  onCancel,
  onSubmit
}: {
  bootstrap: AdminBootstrap;
  mode: UserFormMode;
  user: AdminUser | null;
  onCancel: () => void;
  onSubmit: (payload: Record<string, FormDataEntryValue | FormDataEntryValue[]>, mode: UserFormMode, targetUser?: string) => Promise<void>;
}) {
  const [roleQuery, setRoleQuery] = useState("");
  const roleGroups = useMemo(() => groupRoles(bootstrap.roles, roleQuery), [bootstrap.roles, roleQuery]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      username: form.get("username") || "",
      password: form.get("password") || "",
      first_name: form.get("first_name") || "",
      last_name: form.get("last_name") || "",
      email: form.get("email") || "",
      phone_number: form.get("phone_number") || "",
      primary_department: form.get("primary_department") || "",
      roles: form.getAll("roles")
    };
    await onSubmit(payload, mode, user?.user);
    if (mode === "create") formElement.reset();
  }

  const selectedRoles = new Set(user?.roles || []);
  return (
    <form className="space-y-5 rounded-md border border-gray-200 bg-white p-5 shadow-panel" onSubmit={submit}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted">
            <ShieldCheck className="h-4 w-4" />
            {mode === "edit" ? "Edit account" : "Add account"}
          </div>
          <h2 className="mt-2 text-lg font-bold text-ink">{mode === "edit" ? user?.username : "Add User"}</h2>
        </div>
        {mode === "edit" && (
          <IconButton label="Cancel edit" onClick={onCancel}>
            <X className="h-4 w-4" />
          </IconButton>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
        <Field name="username" label="Username" defaultValue={user?.username} required />
        <Field name="password" label={mode === "edit" ? "New password" : "Password"} type="password" required={mode === "create"} />
        <Field name="first_name" label="First name" defaultValue={user?.first_name} required />
        <Field name="last_name" label="Last name" defaultValue={user?.last_name} required />
        <Field name="email" label="Email" type="email" defaultValue={user?.email} required />
        <Field name="phone_number" label="Phone" defaultValue={user?.phone_number} required />
        <label className="block">
          <span className="text-sm font-semibold text-ink">Primary department</span>
          <select
            className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            name="primary_department"
            defaultValue={user?.primary_department || ""}
          >
            <option value="">Platform</option>
            {bootstrap.departments.map((department) => (
              <option key={department.key} value={department.key}>
                {department.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="rounded-md border border-gray-200 bg-panel p-4">
        <div className="mb-4 space-y-3">
          <div>
            <h3 className="text-base font-bold text-ink">Role assignment</h3>
            <p className="text-sm text-muted">Only active BEDO platform and department roles are available.</p>
          </div>
          <input
            className="focus-ring w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
            placeholder="Filter roles"
            value={roleQuery}
            onChange={(event) => setRoleQuery(event.target.value)}
          />
        </div>
        <div className="space-y-4">
          {roleGroups.map((group) => (
            <section key={group.title}>
              <div className="mb-2 text-xs font-bold uppercase text-muted">{group.title}</div>
              <div className="flex flex-wrap gap-2">
                {group.roles.map((role) => (
                  <label key={role} className="cursor-pointer">
                    <input className="peer sr-only" type="checkbox" name="roles" value={role} defaultChecked={selectedRoles.has(role)} />
                    <span className="block rounded-md border border-gray-300 bg-white px-3 py-2 text-xs font-semibold text-gray-700 peer-checked:border-ember peer-checked:bg-orange-50 peer-checked:text-ink">
                      {role}
                    </span>
                  </label>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>

      <Button type="submit">
        <Save className="mr-2 h-4 w-4" />
        {mode === "edit" ? "Save user" : "Create user"}
      </Button>
    </form>
  );
}

function Field({
  name,
  label,
  type = "text",
  defaultValue = "",
  required = false
}: {
  name: string;
  label: string;
  type?: string;
  defaultValue?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-semibold text-ink">{label}</span>
      <input
        className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        name={name}
        type={type}
        defaultValue={defaultValue}
        required={required}
        autoComplete={name === "password" ? "new-password" : undefined}
      />
    </label>
  );
}

function SecurityLogs({ initialEvents }: { initialEvents: SecurityEvent[] }) {
  const [events, setEvents] = useState(initialEvents);
  const [filters, setFilters] = useState(emptySecurityFilters);

  function updateFilter(field: keyof SecurityFilterState, value: string) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  async function applyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = await fetch("/api/admin/security-events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filters)
    });
    if (response.ok) {
      const data = await response.json();
      setEvents(data.events);
    }
  }

  return (
    <div className="space-y-4 rounded-md border border-gray-200 bg-white p-5 shadow-panel">
      <div>
        <h2 className="text-lg font-bold text-ink">Security Logs</h2>
        <p className="text-sm text-muted">Filter authentication, user administration, profile, and project assignment events.</p>
      </div>
      <form className="grid gap-3 md:grid-cols-3 xl:grid-cols-6" onSubmit={applyFilters}>
        <FilterInput label="Date from" type="date" value={filters.date_from} onChange={(value) => updateFilter("date_from", value)} />
        <FilterInput label="Date to" type="date" value={filters.date_to} onChange={(value) => updateFilter("date_to", value)} />
        <FilterInput label="Name search" value={filters.search} onChange={(value) => updateFilter("search", value)} />
        <FilterInput label="Event type" value={filters.event_type} onChange={(value) => updateFilter("event_type", value)} />
        <FilterInput label="Actor" value={filters.actor} onChange={(value) => updateFilter("actor", value)} />
        <FilterInput label="Target user" value={filters.target_user} onChange={(value) => updateFilter("target_user", value)} />
        <label className="block">
          <span className="text-xs font-bold uppercase text-muted">Status</span>
          <select
            className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            value={filters.status}
            onChange={(event) => updateFilter("status", event.target.value)}
          >
            <option value="">Any</option>
            <option value="Success">Success</option>
            <option value="Failure">Failure</option>
          </select>
        </label>
        <div className="flex items-end gap-2 xl:col-span-5">
          <Button type="submit">Apply filters</Button>
          <Button
            variant="secondary"
            type="button"
            onClick={() => {
              setFilters(emptySecurityFilters);
              setEvents(initialEvents);
            }}
          >
            Clear
          </Button>
        </div>
      </form>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-xs uppercase text-muted">
            <tr>
              <th className="py-3 pr-4">Event</th>
              <th className="py-3 pr-4">Actor</th>
              <th className="py-3 pr-4">Target</th>
              <th className="py-3 pr-4">Status</th>
              <th className="py-3 pr-4">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {events.map((event) => (
              <tr key={`${event.event_type}-${event.created_at}-${event.user}-${event.target_user}`}>
                <td className="py-3 pr-4">{event.event_type}</td>
                <td className="py-3 pr-4">{event.user || event.username || "Unknown"}</td>
                <td className="py-3 pr-4">{event.target_username || event.target_user || "None"}</td>
                <td className="py-3 pr-4">{event.status}</td>
                <td className="py-3 pr-4">{event.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FilterInput({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="text-xs font-bold uppercase text-muted">{label}</span>
      <input
        className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function DeleteUserConfirmModal({
  user,
  onClose,
  onConfirm,
}: {
  user: AdminUser;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4" role="dialog" aria-modal="true" aria-label="Delete user confirmation">
      <div className="w-full max-w-md rounded-md border border-slate-200 bg-white shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-red-700">Delete User</div>
            <h2 className="mt-1 text-xl font-black text-slate-950">{user.first_name} {user.last_name}</h2>
            <p className="mt-1 text-sm font-semibold text-slate-600">{user.username} - {user.email}</p>
          </div>
          <button className="focus-ring rounded-md p-2 text-slate-500 hover:bg-slate-100" type="button" onClick={onClose} aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-5 py-4 text-sm font-semibold leading-6 text-slate-700">
          This removes the BEDO account if the backend confirms it is safe to delete. Protected users remain blocked by the existing API behavior.
        </div>
        <div className="flex justify-end gap-3 border-t border-slate-200 px-5 py-4">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button variant="danger" type="button" onClick={onConfirm}>Delete user</Button>
        </div>
      </div>
    </div>
  );
}

function IconButton({ label, disabled, onClick, children }: { label: string; disabled?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
      type="button"
      title={label}
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function groupRoles(roles: string[], query: string) {
  const groups = new Map<string, string[]>();
  const needle = query.toLowerCase().trim();
  roles
    .filter((role) => !needle || role.toLowerCase().includes(needle))
    .forEach((role) => {
      const title = roleGroupTitle(role);
      groups.set(title, [...(groups.get(title) || []), role]);
    });
  return Array.from(groups.entries()).map(([title, groupRoles]) => ({ title, roles: groupRoles }));
}

function roleGroupTitle(role: string) {
  if (role.startsWith("BEDO")) return "Platform";
  if (role === "General Manager") return "GM Support Office";
  if (role.startsWith("SRS")) return "SRS";
  if (role.startsWith("ARD")) return "ARD";
  return "Other";
}
