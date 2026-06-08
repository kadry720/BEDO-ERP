import { TrainerWorkspace } from "@/features/srs/TrainerWorkspace";
import type { SrsFlowchartDefinition, TrainerWorkspace as TrainerWorkspaceData } from "@/features/srs/types";
import type { BedoUserContext } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { decodedRouteParam } from "@/server/route-params";
import { requireSession } from "@/server/session";

export default async function Page({ params }: { params: Promise<{ trainerItemId: string }> }) {
  const session = await requireSession();
  const { trainerItemId } = await params;
  const trainerItemName = decodedRouteParam(trainerItemId);
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);
  const workspace = await frappeCall<TrainerWorkspaceData>("bedo_platform.api.web.get_trainer_item_workspace", { trainer_item: trainerItemName }, session.user);
  const flowchart = await frappeCall<SrsFlowchartDefinition>("bedo_platform.api.web.get_srs_flowchart_definition", {}, session.user);
  return <TrainerWorkspace session={freshSession} initialWorkspace={workspace} flowchart={flowchart} />;
}
