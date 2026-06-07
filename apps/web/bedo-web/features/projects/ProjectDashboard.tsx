"use client";

import { useEffect, useMemo, useState } from "react";
import { ClipboardList, Send } from "lucide-react";
import { Button } from "@/components/Button";
import type { BedoUserContext } from "@/lib/routes";

type ProjectAssignment = {
  project: string;
  stage: string;
  assigned_by: string;
  assigned_to_user: string;
  assigned_to_role: string;
  team?: string;
  assigned_at: string;
  is_active: number;
};

type Project = {
  name: string;
  project_name: string;
  department_key: string;
  section: string;
  details: string;
  current_stage: string;
  created_by_user: string;
  modified: string;
  assignments: ProjectAssignment[];
};

type AssignableUser = {
  user: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
};

export type ProjectList = {
  projects: Project[];
  page: number;
  page_size: number;
  total: number;
};

const sectionOptions = ["Electronics", "Mechanics", "Software", "Control", "Electrical Power", "Mechatronics", "Documentation", "Graphics and Art"];

export function ProjectDashboard({ session, initialProjects, title }: { session: BedoUserContext; initialProjects: ProjectList; title: string }) {
  const [projects, setProjects] = useState(initialProjects.projects);
  const [assignable, setAssignable] = useState<Record<string, AssignableUser[]>>({});
  const roles = new Set(session.roles);

  const canCreate = roles.has("General Manager");
  const projectCount = projects.length;

  async function refreshProjects(data?: ProjectList) {
    if (data) {
      setProjects(data.projects);
      return;
    }
    const response = await fetch("/api/projects");
    if (response.ok) {
      const next = await response.json();
      setProjects(next.projects);
    }
  }

  async function createProject(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const response = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: form.get("project_name"),
        section: form.get("section"),
        details: form.get("details")
      })
    });
    if (response.ok) {
      const data = await response.json();
      await refreshProjects(data);
      formElement.reset();
    }
  }

  async function loadAssignable(stage: string) {
    if (assignable[stage]) return;
    const response = await fetch(`/api/projects/assignable?stage=${encodeURIComponent(stage)}`);
    if (response.ok) {
      const data = await response.json();
      setAssignable((current) => ({ ...current, [stage]: data.users }));
    }
  }

  useEffect(() => {
    const stages = new Set(projects.map((project) => nextStageForProject(project, session)).filter(Boolean) as string[]);
    stages.forEach((stage) => {
      void loadAssignable(stage);
    });
  }, [projects]);

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted">
          <ClipboardList className="h-4 w-4" />
          Project assignment
        </div>
        <h1 className="mt-2 text-3xl font-bold text-ink">{title}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
          Assignment controls visibility in this phase. Section metadata is descriptive; users see projects because they are assigned.
        </p>
      </header>

      {canCreate && (
        <form className="grid gap-4 rounded-md border border-gray-200 bg-white p-5 shadow-panel lg:grid-cols-[1fr_220px_1.5fr_auto]" onSubmit={createProject}>
          <label className="block">
            <span className="text-sm font-semibold text-ink">Project name</span>
            <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="project_name" required />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-ink">Section</span>
            <select className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="section" required>
              {sectionOptions.map((section) => (
                <option key={section} value={section}>
                  {section}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-ink">Details</span>
            <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="details" />
          </label>
          <div className="flex items-end">
            <Button type="submit">Create</Button>
          </div>
        </form>
      )}

      <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-ink">Projects</h2>
            <p className="text-sm text-muted">{projectCount} visible projects</p>
          </div>
          <Button variant="secondary" type="button" onClick={() => refreshProjects()}>
            Refresh
          </Button>
        </div>
        <div className="space-y-3">
          {projects.map((project) => (
            <ProjectRow
              key={project.name}
              project={project}
              session={session}
              assignable={assignable}
              onAssigned={(data) => refreshProjects(data)}
            />
          ))}
          {!projects.length && <div className="rounded-md border border-dashed border-gray-300 p-6 text-sm text-muted">No visible projects.</div>}
        </div>
      </div>
    </section>
  );
}

function ProjectRow({
  project,
  session,
  assignable,
  onAssigned
}: {
  project: Project;
  session: BedoUserContext;
  assignable: Record<string, AssignableUser[]>;
  onAssigned: (data: ProjectList) => void;
}) {
  const stage = nextStageForProject(project, session);
  const [selected, setSelected] = useState<string[]>([]);
  const candidates = stage ? assignable[stage] || [] : [];

  useEffect(() => {
    setSelected([]);
  }, [stage]);

  async function assign() {
    if (!stage || !selected.length) return;
    const response = await fetch("/api/projects/assign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: project.name, stage, target_users: selected })
    });
    if (response.ok) {
      const data = await response.json();
      onAssigned(data);
    }
  }

  return (
    <article className="grid gap-4 rounded-md border border-gray-200 p-4 xl:grid-cols-[1fr_360px]">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-base font-bold text-ink">{project.project_name}</h3>
          <span className="rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-700">{project.section}</span>
          <span className="rounded bg-orange-50 px-2 py-1 text-xs font-semibold text-ink">{project.current_stage}</span>
        </div>
        {project.details && <p className="mt-2 text-sm leading-6 text-muted">{project.details}</p>}
        <div className="mt-3 flex flex-wrap gap-2">
          {project.assignments.map((assignment) => (
            <span key={`${assignment.stage}-${assignment.assigned_to_user}`} className="rounded border border-gray-200 px-2 py-1 text-xs text-muted">
              {assignment.stage}: {assignment.assigned_to_user}
            </span>
          ))}
        </div>
      </div>
      <div className="rounded-md border border-gray-200 bg-panel p-3">
        {stage ? (
          <div className="space-y-3">
            <div>
              <div className="text-xs font-bold uppercase text-muted">Next assignment</div>
              <div className="mt-1 text-sm font-semibold text-ink">{stage}</div>
            </div>
            {stage === "ARD Engineer" ? (
              <div className="grid max-h-36 gap-2 overflow-y-auto">
                {candidates.map((candidate) => (
                  <label key={candidate.user} className="flex cursor-pointer items-center gap-2 rounded-md bg-white px-3 py-2 text-sm">
                    <input
                      className="accent-ember"
                      type="checkbox"
                      checked={selected.includes(candidate.user)}
                      onChange={(event) => {
                        setSelected((current) =>
                          event.target.checked ? [...current, candidate.user] : current.filter((user) => user !== candidate.user)
                        );
                      }}
                    />
                    {candidate.username}
                  </label>
                ))}
              </div>
            ) : (
              <select
                className="focus-ring w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                value={selected[0] || ""}
                onChange={(event) => setSelected(event.target.value ? [event.target.value] : [])}
              >
                <option value="">Select user</option>
                {candidates.map((candidate) => (
                  <option key={candidate.user} value={candidate.user}>
                    {candidate.username}
                  </option>
                ))}
              </select>
            )}
            <Button type="button" disabled={!selected.length} onClick={assign}>
              <Send className="h-4 w-4" />
              Assign
            </Button>
          </div>
        ) : (
          <div className="text-sm text-muted">No available action for your role on this project.</div>
        )}
      </div>
    </article>
  );
}

function nextStageForProject(project: Project, session: BedoUserContext) {
  const roles = new Set(session.roles);
  const assigned = (stage: string, user = session.user) =>
    project.assignments.some((assignment) => assignment.stage === stage && assignment.assigned_to_user === user && assignment.is_active);
  const hasStage = (stage: string) => project.assignments.some((assignment) => assignment.stage === stage && assignment.is_active);

  if (roles.has("General Manager") && !hasStage("ARD Manager")) return "ARD Manager";
  if (roles.has("ARD Manager") && assigned("ARD Manager") && !hasStage("ARD Section Head")) return "ARD Section Head";
  if (roles.has("ARD Section Head") && assigned("ARD Section Head") && !hasStage("ARD Team Leader")) return "ARD Team Leader";
  if (roles.has("ARD Team Leader") && assigned("ARD Team Leader") && !hasStage("ARD Engineer")) return "ARD Engineer";
  return "";
}
