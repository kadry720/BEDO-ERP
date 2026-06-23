"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ClipboardList, Edit3, Eye, FilePenLine, Plus, RefreshCw, Trash2, X } from "lucide-react";
import { Button } from "@/components/Button";
import { projectWorkflowRoute, routeSegment } from "@/lib/route-ids";
import type { BedoProject, DashboardProps, ProjectList } from "@/features/srs/types";

type ProjectBucket = BedoProject & {
  trainerTotal: number;
  trainerComplete: number;
  progress: number;
  draft: boolean;
  done: boolean;
};

export function ProjectDashboard({ session, initialProjects, mode }: DashboardProps) {
  const [projects, setProjects] = useState<ProjectList>(initialProjects);
  const [editing, setEditing] = useState<BedoProject | null>(null);
  const [deleting, setDeleting] = useState<BedoProject | null>(null);
  const [error, setError] = useState("");
  const baseRoute = mode === "gm" ? "/gm" : mode === "srs" ? "/srs" : mode === "ard" ? "/ard" : "/command-center";
  const isGm = mode === "gm";
  const dashboardLabel = isGm ? "GM Support Office" : mode === "srs" ? "Strategic R&D Sector" : mode === "ard" ? "Applied R&D" : "Command Center";
  const dashboardTitle = isGm ? "GM Support Office Dashboard" : mode === "srs" ? "SRS Dashboard" : mode === "ard" ? "ARD Dashboard" : "Command Center Dashboard";
  const dashboardDescription = isGm
    ? "Project completion is calculated from SRS-completed trainer items."
    : mode === "srs"
      ? "Projects visible to your SRS role and assignments."
      : mode === "ard"
        ? "Projects whose ARD handover has successfully started."
      : "Read-only project visibility with action access limited to the Command Center node.";
  const canManageProjects = isGm && session.roles.includes("General Manager");
  const canViewProjectMetrics = isGm || session.roles.includes("SRS Manager") || session.roles.includes("ARD Manager");

  const buckets = useMemo(() => projects.projects.map(toProjectBucket), [projects]);
  const drafts = buckets.filter((project) => project.draft);
  const ongoing = buckets.filter((project) => !project.draft && !project.done);
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
              {dashboardLabel}
            </div>
            <h2 className="mt-2 text-3xl font-black text-slate-950">{dashboardTitle}</h2>
            <p className="mt-2 text-sm font-medium text-slate-600">
              {dashboardDescription}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" type="button" onClick={refresh}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            {canManageProjects && (
              <Link className="focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white transition hover:bg-steel" href="/gm/projects/new">
                <Plus className="h-4 w-4" />
                Add New Project
              </Link>
            )}
          </div>
        </div>
      </header>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      {isGm && <ProjectCompletionVisual doneCount={done.length} ongoingCount={ongoing.length} draftCount={drafts.length} percentage={completionPercentage} />}

      {isGm && (
        <ProjectTable
          title="Draft Projects"
          description="Saved project setup that has not been released to SRS yet."
          projects={drafts}
          mode={mode}
          baseRoute={baseRoute}
          canManage={canManageProjects}
          showMetrics={canViewProjectMetrics}
          onEdit={setEditing}
          onDelete={setDeleting}
        />
      )}

      <ProjectTable
        title={isGm ? "Ongoing Projects" : mode === "srs" ? "Projects in SRS" : mode === "ard" ? "Projects in ARD" : "Projects"}
        description={isGm ? "Released projects currently moving through SRS." : mode === "srs" ? "Projects visible to your SRS role and assignments." : mode === "ard" ? "Projects with active ARD workflow handover." : "All projects visible to Command Center."}
        projects={isGm ? ongoing : buckets}
        mode={mode}
        baseRoute={baseRoute}
        canManage={canManageProjects}
        showMetrics={canViewProjectMetrics}
        onEdit={setEditing}
        onDelete={setDeleting}
      />

      {isGm && (
        <ProjectTable
          title="Done Projects"
          description="Projects where all trainer items are complete."
          projects={done}
          mode={mode}
          baseRoute={baseRoute}
          canManage={canManageProjects}
          showMetrics={canViewProjectMetrics}
          onEdit={setEditing}
          onDelete={setDeleting}
        />
      )}

      {editing && <EditProjectModal project={editing} onClose={() => setEditing(null)} onSubmit={(payload) => saveProject(editing, payload)} />}
      {deleting && <DeleteProjectConfirmModal project={deleting} onClose={() => setDeleting(null)} onConfirm={() => deleteProject(deleting)} />}
    </section>
  );
}

function ProjectCompletionVisual({ doneCount, ongoingCount, draftCount, percentage }: { doneCount: number; ongoingCount: number; draftCount: number; percentage: number }) {
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
      <div className="grid gap-4 sm:grid-cols-3">
        <Metric label="Draft Projects" value={draftCount} tone="blue" />
        <Metric label="Done Projects" value={doneCount} tone="green" />
        <Metric label="Ongoing Projects" value={ongoingCount} tone="amber" />
      </div>
    </section>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: "green" | "amber" | "blue" }) {
  const color = {
    green: "text-emerald-700",
    amber: "text-amber-700",
    blue: "text-blue-700",
  }[tone];
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-3 text-4xl font-black ${color}`}>{value}</div>
    </div>
  );
}

function ProjectTable({
  title,
  description,
  projects,
  mode,
  baseRoute,
  canManage,
  showMetrics,
  onEdit,
  onDelete,
}: {
  title: string;
  description: string;
  projects: ProjectBucket[];
  mode: "gm" | "srs" | "command-center" | "ard";
  baseRoute: string;
  canManage: boolean;
  showMetrics: boolean;
  onEdit: (project: BedoProject) => void;
  onDelete: (project: BedoProject) => void;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="border-b border-slate-200 px-5 py-4">
        <h3 className="text-lg font-black text-slate-950">{title}</h3>
        <p className="text-sm font-medium text-slate-500">
          {description} {projects.length} project(s)
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className={`w-full table-fixed text-left text-sm ${showMetrics ? "min-w-[1160px]" : "min-w-[760px]"}`}>
          <colgroup>
            {showMetrics ? (
              <>
                <col className="w-[150px]" />
                <col className="w-[260px]" />
                <col className="w-[220px]" />
                <col className="w-[130px]" />
                <col className="w-[90px]" />
                <col className="w-[160px]" />
                <col className="w-[150px]" />
              </>
            ) : (
              <>
                <col className="w-[170px]" />
                <col className="w-[320px]" />
                <col className="w-[230px]" />
                <col className="w-[120px]" />
              </>
            )}
          </colgroup>
          <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-black uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Project Code</th>
              <th className="px-4 py-3">Project Name</th>
              <th className="px-4 py-3">End User</th>
              {showMetrics && (
                <>
                  <th className="px-4 py-3">PO Deadline</th>
                  <th className="px-4 py-3">Trainers</th>
                  <th className="px-4 py-3">Progress</th>
                </>
              )}
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {projects.map((project) => (
              <tr key={project.name} className="hover:bg-slate-50">
                <td className="truncate px-4 py-3 font-black text-slate-950" title={project.project_code}>
                  {project.project_code}
                </td>
                <td className="truncate px-4 py-3 font-semibold text-slate-700" title={project.project_name}>
                  {project.project_name}
                </td>
                <td className="truncate px-4 py-3 text-slate-600" title={project.end_user}>
                  {project.end_user}
                </td>
                {showMetrics && (
                  <>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-600">{project.po_deadline_date}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-semibold text-slate-700">{project.trainerTotal}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                          <div className="h-full rounded-full bg-slate-900" style={{ width: `${project.progress}%` }} />
                        </div>
                        <span className="w-10 text-right text-xs font-black text-slate-700">{project.progress}%</span>
                      </div>
                    </td>
                  </>
                )}
                <td className="px-3 py-3">
                  <div className="flex items-center justify-end gap-2">
                    {canManage && (
                      <>
                        <button
                          className="focus-ring inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-800 hover:bg-slate-50"
                          type="button"
                          title="Edit"
                          aria-label="Edit project"
                          onClick={() => onEdit(project)}
                        >
                          <Edit3 className="h-4 w-4" />
                        </button>
                        <button
                          className="focus-ring inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-red-700 text-white hover:bg-red-800"
                          type="button"
                          title="Delete"
                          aria-label="Delete project"
                          onClick={() => onDelete(project)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </>
                    )}
                    {project.draft && canManage ? (
                      <Link
                        className="focus-ring inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-slate-900 text-white hover:bg-slate-700"
                        href={`${baseRoute}/projects/${routeSegment(project.name)}/resume`}
                        title="Resume draft"
                        aria-label="Resume draft"
                      >
                        <FilePenLine className="h-4 w-4" />
                      </Link>
                    ) : (
                      <Link
                        className="focus-ring inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-800 hover:bg-slate-50"
                        href={projectWorkflowRoute(mode, project.name, "/trainers")}
                        title="View trainers"
                        aria-label="View trainers"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                    )}
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
  const draft = project.status === "DETAILS_FINALIZED" || !project.released_to_srs_at;
  return {
    ...project,
    trainerTotal,
    trainerComplete,
    progress,
    draft,
    done: !draft && trainerTotal > 0 && trainerComplete === trainerTotal,
  };
}
