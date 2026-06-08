"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ClipboardList, Edit3, Eye, Plus, RefreshCw, Trash2, X } from "lucide-react";
import { Button } from "@/components/Button";
import { routeSegment } from "@/lib/route-ids";
import type { BedoProject, DashboardProps, ProjectList } from "@/features/srs/types";

type ProjectBucket = BedoProject & {
  trainerTotal: number;
  trainerComplete: number;
  progress: number;
  done: boolean;
};

export function ProjectDashboard({ initialProjects, mode }: DashboardProps) {
  const [projects, setProjects] = useState<ProjectList>(initialProjects);
  const [editing, setEditing] = useState<BedoProject | null>(null);
  const [deleting, setDeleting] = useState<BedoProject | null>(null);
  const [error, setError] = useState("");
  const baseRoute = mode === "gm" ? "/gm" : "/srs";
  const isGm = mode === "gm";

  const buckets = useMemo(() => projects.projects.map(toProjectBucket), [projects]);
  const ongoing = buckets.filter((project) => !project.done);
  const done = buckets.filter((project) => project.done);
  const completionPercentage = buckets.length ? Math.round((done.length / buckets.length) * 100) : 0;

  async function refresh() {
    const response = await fetch("/api/projects?page_size=100");
    if (response.ok) setProjects(await response.json());
  }

  async function saveProject(project: BedoProject, payload: Record<string, unknown>) {
    setError("");
    const response = await fetch(`/api/projects/${routeSegment(project.name)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      setError("Project could not be updated.");
      return;
    }
    setEditing(null);
    await refresh();
  }

  async function deleteProject(project: BedoProject) {
    setError("");
    const response = await fetch(`/api/projects/${routeSegment(project.name)}`, { method: "DELETE" });
    if (!response.ok) {
      setError("Project could not be deleted.");
      return;
    }
    setDeleting(null);
    await refresh();
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500">
              <ClipboardList className="h-4 w-4" />
              {isGm ? "GM Support Office" : "Strategic R&D Sector"}
            </div>
            <h2 className="mt-2 text-3xl font-black text-slate-950">{isGm ? "GM Support Office Dashboard" : "SRS Dashboard"}</h2>
            <p className="mt-2 text-sm font-medium text-slate-600">
              {isGm ? "Project completion is calculated from SRS-completed trainer items." : "Projects visible to your SRS role and assignments."}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" type="button" onClick={refresh}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            {isGm && (
              <Link className="focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white transition hover:bg-steel" href="/gm/projects/new">
                <Plus className="h-4 w-4" />
                Add New Project
              </Link>
            )}
          </div>
        </div>
      </header>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      {isGm && <ProjectCompletionVisual doneCount={done.length} ongoingCount={ongoing.length} percentage={completionPercentage} />}

      <ProjectTable
        title={isGm ? "Ongoing Projects" : "Projects in SRS"}
        projects={isGm ? ongoing : buckets}
        baseRoute={baseRoute}
        canManage={isGm}
        onEdit={setEditing}
        onDelete={setDeleting}
      />

      {isGm && <ProjectTable title="Done Projects" projects={done} baseRoute={baseRoute} canManage onEdit={setEditing} onDelete={setDeleting} />}

      {editing && <EditProjectModal project={editing} onClose={() => setEditing(null)} onSubmit={(payload) => saveProject(editing, payload)} />}
      {deleting && <DeleteProjectConfirmModal project={deleting} onClose={() => setDeleting(null)} onConfirm={() => deleteProject(deleting)} />}
    </section>
  );
}

function ProjectCompletionVisual({ doneCount, ongoingCount, percentage }: { doneCount: number; ongoingCount: number; percentage: number }) {
  return (
    <section className="grid gap-4 lg:grid-cols-[280px_1fr]">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">Completion</div>
        <div className="mt-4 flex items-end gap-2">
          <span className="text-5xl font-black text-slate-950">{percentage}</span>
          <span className="pb-2 text-lg font-black text-slate-500">%</span>
        </div>
        <div className="mt-5 h-3 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-emerald-600" style={{ width: `${percentage}%` }} />
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Metric label="Done Projects" value={doneCount} tone="green" />
        <Metric label="Ongoing Projects" value={ongoingCount} tone="amber" />
      </div>
    </section>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: "green" | "amber" }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-3 text-4xl font-black ${tone === "green" ? "text-emerald-700" : "text-amber-700"}`}>{value}</div>
    </div>
  );
}

function ProjectTable({
  title,
  projects,
  baseRoute,
  canManage,
  onEdit,
  onDelete,
}: {
  title: string;
  projects: ProjectBucket[];
  baseRoute: string;
  canManage: boolean;
  onEdit: (project: BedoProject) => void;
  onDelete: (project: BedoProject) => void;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="border-b border-slate-200 px-5 py-4">
        <h3 className="text-lg font-black text-slate-950">{title}</h3>
        <p className="text-sm font-medium text-slate-500">{projects.length} project(s)</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[980px] w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-black uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Project Code</th>
              <th className="px-4 py-3">Project Name</th>
              <th className="px-4 py-3">End User</th>
              <th className="px-4 py-3">PO Deadline</th>
              <th className="px-4 py-3">Trainers</th>
              <th className="px-4 py-3">Progress</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {projects.map((project) => (
              <tr key={project.name} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-black text-slate-950">{project.project_code}</td>
                <td className="max-w-[260px] truncate px-4 py-3 font-semibold text-slate-700" title={project.project_name}>{project.project_name}</td>
                <td className="max-w-[220px] truncate px-4 py-3 text-slate-600" title={project.end_user}>{project.end_user}</td>
                <td className="px-4 py-3 text-slate-600">{project.po_deadline_date}</td>
                <td className="px-4 py-3 font-semibold text-slate-700">{project.trainerTotal}</td>
                <td className="px-4 py-3">
                  <div className="flex min-w-36 items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-slate-900" style={{ width: `${project.progress}%` }} />
                    </div>
                    <span className="w-10 text-right text-xs font-black text-slate-700">{project.progress}%</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    {canManage && (
                      <>
                        <Button className="min-h-9 px-3" variant="secondary" type="button" onClick={() => onEdit(project)}>
                          <Edit3 className="h-4 w-4" />
                          Edit
                        </Button>
                        <Button className="min-h-9 px-3" variant="danger" type="button" onClick={() => onDelete(project)}>
                          <Trash2 className="h-4 w-4" />
                          Delete
                        </Button>
                      </>
                    )}
                    <Link className="focus-ring inline-flex min-h-9 items-center gap-2 rounded-md border border-slate-300 bg-white px-3 text-xs font-black text-slate-700 hover:bg-slate-50" href={`${baseRoute}/projects/${routeSegment(project.name)}/trainers`}>
                      <Eye className="h-4 w-4" />
                      View Trainers Table
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!projects.length && <div className="m-5 rounded-md border border-dashed border-slate-300 p-8 text-center text-sm font-bold text-slate-500">No projects to show.</div>}
      </div>
    </section>
  );
}

function EditProjectModal({ project, onClose, onSubmit }: { project: BedoProject; onClose: () => void; onSubmit: (payload: Record<string, unknown>) => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <form
        className="w-full max-w-2xl rounded-lg bg-white shadow-2xl"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          onSubmit({
            project_name: form.get("project_name"),
            project_code: form.get("project_code"),
            end_user: form.get("end_user"),
            po_deadline_date: form.get("po_deadline_date"),
          });
        }}
      >
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">Edit Project</div>
            <h3 className="mt-1 text-xl font-black text-slate-950">{project.project_code}</h3>
          </div>
          <button className="rounded-md p-2 text-slate-500 hover:bg-slate-100" type="button" onClick={onClose} aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="grid gap-4 px-6 py-5 md:grid-cols-2">
          <Field name="project_name" label="Project Name" defaultValue={project.project_name} />
          <Field name="project_code" label="Project Code" defaultValue={project.project_code} />
          <Field name="end_user" label="End User" defaultValue={project.end_user} />
          <Field name="po_deadline_date" label="PO Deadline Date" type="date" defaultValue={project.po_deadline_date} />
        </div>
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit">Save Project</Button>
        </div>
      </form>
    </div>
  );
}

function DeleteProjectConfirmModal({ project, onClose, onConfirm }: { project: BedoProject; onClose: () => void; onConfirm: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <div className="w-full max-w-md rounded-lg bg-white shadow-2xl">
        <div className="border-b border-slate-200 px-6 py-5">
          <div className="text-xs font-black uppercase tracking-wide text-red-600">Delete Project</div>
          <h3 className="mt-1 text-xl font-black text-slate-950">{project.project_code}</h3>
        </div>
        <div className="px-6 py-5">
          <p className="text-sm leading-6 text-slate-600">
            This will remove the project, trainer items, SRS workflow rows, approvals, notifications, and deadlines for this project.
          </p>
        </div>
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button variant="danger" type="button" onClick={onConfirm}>Delete Project</Button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  name,
  type = "text",
  defaultValue,
}: {
  label: string;
  name: string;
  type?: string;
  defaultValue?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-black text-slate-800">{label}</span>
      <input className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} name={name} defaultValue={defaultValue} />
    </label>
  );
}

function toProjectBucket(project: BedoProject): ProjectBucket {
  const trainerTotal = project.counts?.trainer_items || 0;
  const trainerComplete = project.counts?.completed || 0;
  const progress = trainerTotal ? Math.round((trainerComplete / trainerTotal) * 100) : 0;
  return {
    ...project,
    trainerTotal,
    trainerComplete,
    progress,
    done: trainerTotal > 0 && trainerComplete === trainerTotal,
  };
}
