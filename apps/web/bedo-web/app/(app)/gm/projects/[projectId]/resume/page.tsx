import { redirect } from "next/navigation";
import { AddProjectPage } from "@/features/srs/AddProjectPage";
import type { SafeUser } from "@/features/srs/types";
import { frappeCall } from "@/server/frappe";
import { loadProjectDetailOrForbidden, requireProjectScope, routeProjectName } from "@/server/project-pages";

export default async function Page({ params }: { params: Promise<{ projectId: string }> }) {
  const { session } = await requireProjectScope("gm", { manage: true });

  const { projectId } = await params;
  const projectName = routeProjectName(projectId);
  const [{ project, items }, reportToUsers] = await Promise.all([
    loadProjectDetailOrForbidden(session.user, projectName),
    frappeCall<{ users: SafeUser[] }>("bedo_platform.api.web.list_report_to_candidates", {}, session.user).catch(() => ({ users: [] })),
  ]);

  if (project.project.released_to_srs_at || project.project.status !== "DETAILS_FINALIZED") {
    redirect(`/gm/projects/${encodeURIComponent(project.project.name)}/trainers`);
  }

  return <AddProjectPage reportToUsers={reportToUsers.users} initialProject={project.project} initialTrainers={items.trainer_items} />;
}
