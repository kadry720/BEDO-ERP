import { TrainerWorkspace } from "@/features/srs/TrainerWorkspace";
import { loadTrainerWorkspaceOrForbidden, requireProjectScope, routeProjectName } from "@/server/project-pages";

export default async function Page({ params }: { params: Promise<{ trainerItemId: string }> }) {
  const { session, freshSession } = await requireProjectScope("srs");
  const { trainerItemId } = await params;
  const trainerItemName = routeProjectName(trainerItemId);
  const { workspace, flowchart } = await loadTrainerWorkspaceOrForbidden(session.user, trainerItemName);
  return <TrainerWorkspace session={freshSession} initialWorkspace={workspace} flowchart={flowchart} />;
}
