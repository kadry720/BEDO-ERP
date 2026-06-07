"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { ClipboardList, Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/Button";
import type { DashboardProps, ProjectList } from "@/features/srs/types";
import { formatStatus, statusBadgeClass } from "@/features/srs/workflowPresentation";

export function ProjectDashboard({ session, initialProjects, mode }: DashboardProps) {
  const router = useRouter();
  const [projects, setProjects] = useState<ProjectList>(initialProjects);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState("");
  const canCreate = mode === "gm" && session.roles.includes("General Manager");
  const baseRoute = mode === "gm" ? "/gm" : "/srs";

  const totals = useMemo(() => {
    return projects.projects.reduce(
      (acc, project) => {
        acc.items += project.counts?.trainer_items || 0;
        acc.waiting += project.counts?.awaiting_owner_assignment || 0;
        acc.approvals += project.counts?.waiting_approval || 0;
        acc.completed += project.counts?.completed || 0;
        return acc;
      },
      { items: 0, waiting: 0, approvals: 0, completed: 0 }
    );
  }, [projects]);

  async function refresh() {
    const response = await fetch("/api/projects");
    if (response.ok) setProjects(await response.json());
  }

  async function createProject(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      project_name: form.get("project_name"),
      project_code: form.get("project_code"),
      end_user: form.get("end_user"),
      po_deadline_date: form.get("po_deadline_date")
    };
    const response = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      setError("Project could not be created. Check required fields and project code uniqueness.");
      return;
    }
    const data = await response.json();
    formElement.reset();
    router.push(`/gm/projects/${data.project}`);
  }

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted">
              <ClipboardList className="h-4 w-4" />
              {mode === "gm" ? "GM Support Office" : "Strategic R&D Sector"}
            </div>
            <h1 className="mt-2 text-3xl font-bold text-ink">{mode === "gm" ? "GM Support Office Dashboard" : "SRS Dashboard"}</h1>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" type="button" onClick={refresh}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            {canCreate && (
              <Button type="button" onClick={() => setShowCreate((value) => !value)}>
                <Plus className="h-4 w-4" />
                Add New Project
              </Button>
            )}
          </div>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Projects" value={projects.total} />
        <Metric label="Trainer Items" value={totals.items} />
        <Metric label="Awaiting Owner" value={totals.waiting} />
        <Metric label="Waiting Approval" value={totals.approvals} />
      </div>

      {showCreate && canCreate && (
        <form className="rounded-md border border-gray-200 bg-white p-5 shadow-panel" onSubmit={createProject}>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Field name="project_name" label="Project Name" required />
            <Field name="project_code" label="Project Code" required />
            <Field name="end_user" label="End User" required />
            <Field name="po_deadline_date" label="PO Deadline Date" type="date" required />
          </div>
          {error && <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">{error}</div>}
          <div className="mt-4">
            <Button type="submit">Create Project</Button>
          </div>
        </form>
      )}

      <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
        <div className="mb-4">
          <h2 className="text-lg font-bold text-ink">{mode === "gm" ? "Ongoing Projects" : "Projects in SRS"}</h2>
          <p className="text-sm text-muted">Project rows open into trainer-item tables. Flowcharts live only inside trainer items.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-xs uppercase text-muted">
              <tr>
                <th className="py-3 pr-4">Project Code</th>
                <th className="py-3 pr-4">Project Name</th>
                <th className="py-3 pr-4">End User</th>
                <th className="py-3 pr-4">PO Deadline</th>
                <th className="py-3 pr-4">Trainer Items</th>
                <th className="py-3 pr-4">SRS Progress</th>
                <th className="py-3 pr-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {projects.projects.map((project) => (
                <tr key={project.name} className="hover:bg-gray-50">
                  <td className="py-3 pr-4 font-semibold text-ink">
                    <Link href={`${baseRoute}/projects/${project.name}`}>{project.project_code}</Link>
                  </td>
                  <td className="py-3 pr-4">{project.project_name}</td>
                  <td className="py-3 pr-4">{project.end_user}</td>
                  <td className="py-3 pr-4">{project.po_deadline_date}</td>
                  <td className="py-3 pr-4">{project.counts?.trainer_items || 0}</td>
                  <td className="py-3 pr-4">
                    <div className="flex flex-wrap gap-1">
                      <Badge label="Owner" value={project.counts?.awaiting_owner_assignment || 0} />
                      <Badge label="Approval" value={project.counts?.waiting_approval || 0} />
                      <Badge label="Done" value={project.counts?.completed || 0} />
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-bold ${statusBadgeClass(project.status)}`}>
                      {formatStatus(project.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!projects.projects.length && <div className="rounded-md border border-dashed border-gray-300 p-6 text-sm text-muted">No projects to show.</div>}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-4 shadow-panel">
      <div className="text-xs font-bold uppercase text-muted">{label}</div>
      <div className="mt-2 text-2xl font-bold text-ink">{value}</div>
    </div>
  );
}

function Field({ label, name, type = "text", required = false }: { label: string; name: string; type?: string; required?: boolean }) {
  return (
    <label className="block">
      <span className="text-sm font-semibold text-ink">{label}</span>
      <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" type={type} name={name} required={required} />
    </label>
  );
}

function Badge({ label, value }: { label: string; value: number }) {
  return (
    <span className="rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-700">
      {label}: {value}
    </span>
  );
}
