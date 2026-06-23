import { ArdWorkspace } from "@/features/ard/ArdWorkspace";
import { ProjectDetail } from "@/features/srs/ProjectDetail";
import { loadArdWorkspaceOrForbidden, loadProjectDetailOrForbidden, parseNotificationProjectRoute, requireProjectScope } from "@/server/project-pages";

export default async function Page({ params }: { params: Promise<{ parts?: string[] }> }) {
  const { session, freshSession } = await requireProjectScope("ard");
  const { parts = [] } = await params;
  const route = parseNotificationProjectRoute(parts);

  if (route.kind === "item") {
    const { workspace, flowchart } = await loadArdWorkspaceOrForbidden(session.user, route.trainerItemName);
    return <ArdWorkspace initialWorkspace={workspace} flowchart={flowchart} />;
  }

  const { project, items } = await loadProjectDetailOrForbidden(session.user, route.projectName);
  return <ProjectDetail project={project.project} initialItems={items} mode="ard" viewerRoles={freshSession.roles} />;
}
