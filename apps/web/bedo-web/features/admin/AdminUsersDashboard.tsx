"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/Button";
import type { AdminBootstrap, AdminUser, SecurityEvent } from "@/features/admin/types";

const tabs = ["Users", "Roles", "Role Profiles", "Department Access", "Module Access / Permissions", "Security Logs"];

export function AdminUsersDashboard({ bootstrap, securityEvents }: { bootstrap: AdminBootstrap; securityEvents: SecurityEvent[] }) {
  const [activeTab, setActiveTab] = useState(tabs[0]);
  const [users, setUsers] = useState(bootstrap.users);
  const [query, setQuery] = useState("");
  const [roleQuery, setRoleQuery] = useState("");

  const filtered = useMemo(() => {
    const needle = query.toLowerCase().trim();
    const visibleUsers = users.filter((user) => user.user !== "Administrator");
    if (!needle) return visibleUsers;
    return visibleUsers.filter((user) =>
      [user.username, user.first_name, user.last_name, user.email, user.primary_department, user.roles.join(" ")]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    );
  }, [query, users]);

  const roleGroups = useMemo(() => groupRoles(bootstrap.roles, roleQuery), [bootstrap.roles, roleQuery]);

  async function createUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      username: form.get("username"),
      password: form.get("password"),
      first_name: form.get("first_name"),
      last_name: form.get("last_name"),
      email: form.get("email"),
      phone_number: form.get("phone_number"),
      primary_department: form.get("primary_department"),
      roles: form.getAll("roles")
    };
    const response = await fetch("/api/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (response.ok) {
      const data = await response.json();
      setUsers(data.users);
      event.currentTarget.reset();
    }
  }

  async function disableUser(user: AdminUser) {
    const response = await fetch("/api/admin/users", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: user.user, enabled: 0 })
    });
    if (response.ok) {
      setUsers((current) => current.map((row) => (row.user === user.user ? { ...row, enabled: 0 } : row)));
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="text-xs font-semibold uppercase text-muted">Administration</div>
        <h1 className="mt-2 text-3xl font-bold text-ink">User Administration</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
          Manage BEDO accounts, explicit admin access, route visibility, technical Desk access, and security review.
          Business workflow permissions are not implemented in this phase.
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

      {activeTab === "Users" && (
        <div className="space-y-6">
          <form className="space-y-5 rounded-md border border-gray-200 bg-white p-5 shadow-panel" onSubmit={createUser}>
            <div>
              <h2 className="text-lg font-bold text-ink">Add LDAP User</h2>
              <p className="mt-1 text-sm text-muted">Password is input-only and sent to the backend provisioning adapter.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {["username", "password", "first_name", "last_name", "email", "phone_number"].map((field) => (
                <label key={field} className="block">
                  <span className="text-sm font-semibold capitalize text-ink">{field.replaceAll("_", " ")}</span>
                  <input
                    className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    name={field}
                    type={field === "password" ? "password" : "text"}
                    required
                  />
                </label>
              ))}
              <label className="block">
                <span className="text-sm font-semibold text-ink">Primary department</span>
                <select className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="primary_department">
                  {bootstrap.departments.map((department) => (
                    <option key={department.key} value={department.key}>
                      {department.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="rounded-md border border-gray-200 bg-panel p-4">
              <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h3 className="text-base font-bold text-ink">Role assignment</h3>
                  <p className="text-sm text-muted">Choose one or more roles from the grouped access catalog.</p>
                </div>
                <input
                  className="focus-ring w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm md:w-80"
                  placeholder="Filter roles"
                  value={roleQuery}
                  onChange={(event) => setRoleQuery(event.target.value)}
                />
              </div>
              <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
                {roleGroups.map((group) => (
                  <section key={group.title} className="rounded-md border border-gray-200 bg-white p-3">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <h4 className="text-sm font-bold text-ink">{group.title}</h4>
                      <span className="rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-muted">{group.roles.length}</span>
                    </div>
                    <div className="grid max-h-52 gap-2 overflow-y-auto pr-1">
                      {group.roles.map((role) => (
                        <label
                          key={role}
                          className="flex cursor-pointer items-start gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm hover:border-ember hover:bg-orange-50"
                        >
                          <input className="mt-1 accent-ember" type="checkbox" name="roles" value={role} />
                          <span className="font-medium text-gray-700">{role}</span>
                        </label>
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            </div>

            <Button type="submit">Create user</Button>
          </form>

          <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-bold text-ink">Users</h2>
                <p className="text-sm text-muted">{filtered.length} visible accounts</p>
              </div>
              <input
                className="focus-ring w-full rounded-md border border-gray-300 px-3 py-2 text-sm md:w-96"
                placeholder="Search users, roles, departments"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-gray-200 text-xs uppercase text-muted">
                  <tr>
                    <th className="py-3 pr-4">User</th>
                    <th className="py-3 pr-4">Department</th>
                    <th className="py-3 pr-4">Roles</th>
                    <th className="py-3 pr-4">Status</th>
                    <th className="py-3 pr-4"></th>
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
                      </td>
                      <td className="py-4 pr-4">{user.primary_department || "None"}</td>
                      <td className="py-4 pr-4">
                        <div className="flex max-w-4xl flex-wrap gap-1">
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
                        {user.enabled ? (
                          <Button variant="secondary" type="button" onClick={() => disableUser(user)}>
                            Disable
                          </Button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === "Roles" && <MetadataPanel title="Roles" items={bootstrap.roles} />}
      {activeTab === "Role Profiles" && <MetadataPanel title="Role Profiles" items={["Platform", "Department", "Team"]} />}
      {activeTab === "Department Access" && (
        <MetadataPanel title="Department Access" items={bootstrap.departments.map((department) => `${department.key} - ${department.name}`)} />
      )}
      {activeTab === "Module Access / Permissions" && (
        <MetadataPanel
          title="Module Access / Permissions"
          items={[
            "Controls route/module visibility",
            "Controls /admin/users access",
            `Controls Frappe Desk technical access through ${bootstrap.technical_desk_roles.join(", ")}`
          ]}
        />
      )}
      {activeTab === "Security Logs" && <SecurityLogs events={securityEvents} />}
    </section>
  );
}

function SecurityLogs({ events }: { events: SecurityEvent[] }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
      <h2 className="text-lg font-bold text-ink">Security Logs</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-xs uppercase text-muted">
            <tr>
              <th className="py-3 pr-4">Event</th>
              <th className="py-3 pr-4">User</th>
              <th className="py-3 pr-4">Status</th>
              <th className="py-3 pr-4">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {events.map((event) => (
              <tr key={`${event.event_type}-${event.created_at}-${event.user}`}>
                <td className="py-3 pr-4">{event.event_type}</td>
                <td className="py-3 pr-4">{event.user || event.username || "Unknown"}</td>
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

function MetadataPanel({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
      <h2 className="text-lg font-bold text-ink">{title}</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <div key={item} className="rounded-md border border-gray-200 bg-panel px-4 py-3 text-sm font-medium text-gray-700">
            {item}
          </div>
        ))}
      </div>
    </div>
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
  if (role.startsWith("GM") || role === "General Manager") return "GM Support Office";
  if (role.startsWith("SRS")) return "SRS";
  if (role.startsWith("ARD")) return "ARD";
  if (role.startsWith("Command Center")) return "Command Center";
  if (role.startsWith("Production") || role.includes("Production") || role.includes("Hall") || role.includes("Assembly")) return "Production";
  if (role.startsWith("QC") || role.includes("QC") || role.includes("Validation")) return "Quality Control";
  if (role.startsWith("Operations") || role.includes("Project Coordinator") || role.includes("Field Team")) return "Operations";
  if (role.startsWith("Purchasing") || role.includes("Supplier")) return "Purchasing";
  if (role.startsWith("HR") || role.includes("KPI")) return "HR";
  if (role.startsWith("IT") || role.includes("LDAP")) return "IT Administration";
  return "Specialist Roles";
}
