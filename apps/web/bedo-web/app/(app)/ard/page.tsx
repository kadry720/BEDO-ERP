import { redirect } from "next/navigation";
import { ProjectDashboard, type ProjectList } from "@/features/projects/ProjectDashboard";
import type { BedoUserContext } from "@/lib/routes";
import { canAccessRoute } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page() {
  const session = await requireSession();
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);
  if (!canAccessRoute(freshSession, "/ard")) redirect("/forbidden");
  const projects = await frappeCall<ProjectList>(
    "bedo_platform.api.web.list_projects_for_user",
    { page: 1, page_size: 25 },
    session.user
  ).catch(() => ({ projects: [], page: 1, page_size: 25, total: 0 }));
  return <ProjectDashboard session={freshSession} initialProjects={projects} title="ARD" />;
}
