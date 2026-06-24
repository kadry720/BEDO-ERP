import { ArdProjectDetail } from "@/features/ard/ArdProjectDetail";
import { ArdWorkspace } from "@/features/ard/ArdWorkspace";
import { loadArdProjectDetailOrForbidden, loadArdWorkspaceOrForbidden, parseNotificationProjectRoute, requireProjectScope } from "@/server/project-pages";

export default async function Page({ params }: { params: Promise<{ parts?: string[] }> }) {
  const { session } = await requireProjectScope("ard");
  const { parts = [] } = await params;
  const route = parseNotificationProjectRoute(parts);

  if (route.kind === "item") {
    const { workspace, flowchart } = await loadArdWorkspaceOrForbidden(session.user, route.trainerItemName);
    return <ArdWorkspace initialWorkspace={workspace} flowchart={flowchart} />;
  }

  const detail = await loadArdProjectDetailOrForbidden(session.user, route.projectName);
  return <ArdProjectDetail detail={detail} />;
}
