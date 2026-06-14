import { redirect } from "next/navigation";
import type { BedoProject, SrsFlowchartDefinition, TrainerItemList, TrainerWorkspace as TrainerWorkspaceData } from "@/features/srs/types";
import type { BedoUserContext } from "@/lib/routes";
import { canAccessRoute, isGeneralManager, isSrsUser } from "@/lib/routes";
import { decodedRouteParam } from "@/lib/route-ids";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

type ProjectScope = "gm" | "srs" | "command-center";

export function routeProjectName(...parts: string[]) {
  return decodedRouteParam(parts.filter(Boolean).join("/"));
}

export type NotificationProjectRoute =
  | { kind: "project"; projectName: string }
  | { kind: "trainers"; projectName: string }
  | { kind: "item"; projectName: string; trainerItemName: string };

export function parseNotificationProjectRoute(parts: string[] = []): NotificationProjectRoute {
  const itemMarkerIndex = parts.lastIndexOf("items");
  if (itemMarkerIndex >= 0 && itemMarkerIndex < parts.length - 1) {
    return {
      kind: "item",
      projectName: routeProjectName(...parts.slice(0, itemMarkerIndex)),
      trainerItemName: routeProjectName(...parts.slice(itemMarkerIndex + 1)),
    };
  }

  if (parts.at(-1) === "trainers") {
    return {
      kind: "trainers",
      projectName: routeProjectName(...parts.slice(0, -1)),
    };
  }

  return {
    kind: "project",
    projectName: routeProjectName(...parts),
  };
}

export async function requireProjectScope(scope: ProjectScope, options: { manage?: boolean } = {}) {
  const session = await requireSession();
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);

  if (scope === "gm") {
    const allowed = options.manage ? isGeneralManager(freshSession) : canAccessRoute(freshSession, "/gm");
    if (!allowed) redirect("/forbidden");
  } else if (scope === "command-center") {
    if (!canAccessRoute(freshSession, "/command-center")) redirect("/forbidden");
  } else if (!isSrsUser(freshSession)) {
    redirect("/forbidden");
  }

  return { session, freshSession };
}

export async function loadProjectDetailOrForbidden(user: string, projectName: string) {
  try {
    const [project, items] = await Promise.all([
      frappeCall<{ project: BedoProject }>("bedo_platform.api.web.get_project_detail", { project: projectName }, user),
      frappeCall<TrainerItemList>("bedo_platform.api.web.list_trainer_items_for_project", { project: projectName }, user),
    ]);
    return { project, items };
  } catch {
    redirect("/forbidden");
  }
}

export async function loadTrainerWorkspaceOrForbidden(user: string, trainerItemName: string) {
  try {
    const [workspace, flowchart] = await Promise.all([
      frappeCall<TrainerWorkspaceData>("bedo_platform.api.web.get_trainer_item_workspace", { trainer_item: trainerItemName }, user),
      frappeCall<SrsFlowchartDefinition>("bedo_platform.api.web.get_srs_flowchart_definition", {}, user),
    ]);
    return { workspace, flowchart };
  } catch {
    redirect("/forbidden");
  }
}
