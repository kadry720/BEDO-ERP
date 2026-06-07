import { ProjectDetail } from "@/features/srs/ProjectDetail";
import type { BedoProject, TrainerItemList } from "@/features/srs/types";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page({ params }: { params: Promise<{ projectId: string }> }) {
  const session = await requireSession();
  const { projectId } = await params;
  const project = await frappeCall<{ project: BedoProject }>("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  const items = await frappeCall<TrainerItemList>("bedo_platform.api.web.list_trainer_items_for_project", { project: projectId }, session.user);
  return <ProjectDetail project={project.project} initialItems={items} mode="srs" />;
}
