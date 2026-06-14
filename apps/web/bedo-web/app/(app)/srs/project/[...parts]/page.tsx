import { ProjectDetail } from "@/features/srs/ProjectDetail";
import { TrainerWorkspace } from "@/features/srs/TrainerWorkspace";
import { loadProjectDetailOrForbidden, loadTrainerWorkspaceOrForbidden, parseNotificationProjectRoute, requireProjectScope } from "@/server/project-pages";

export default async function Page({ params }: { params: Promise<{ parts?: string[] }> }) {
  const { session, freshSession } = await requireProjectScope("srs");
  const { parts = [] } = await params;
  const route = parseNotificationProjectRoute(parts);

  if (route.kind === "item") {
    const { workspace, flowchart } = await loadTrainerWorkspaceOrForbidden(session.user, route.trainerItemName);
    return <TrainerWorkspace session={freshSession} initialWorkspace={workspace} flowchart={flowchart} />;
  }

  const { project, items } = await loadProjectDetailOrForbidden(session.user, route.projectName);
  return <ProjectDetail project={project.project} initialItems={items} mode="srs" viewerRoles={freshSession.roles} />;
}
