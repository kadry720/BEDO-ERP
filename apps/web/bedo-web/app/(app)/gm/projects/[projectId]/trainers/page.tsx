import { ProjectDetail } from "@/features/srs/ProjectDetail";
import { loadProjectDetailOrForbidden, requireProjectScope, routeProjectName } from "@/server/project-pages";

export default async function Page({ params }: { params: Promise<{ projectId: string }> }) {
  const { session } = await requireProjectScope("gm");
  const { projectId } = await params;
  const projectName = routeProjectName(projectId);
  const { project, items } = await loadProjectDetailOrForbidden(session.user, projectName);
  return <ProjectDetail project={project.project} initialItems={items} mode="gm" />;
}
