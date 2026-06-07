import { joinedProjectId, releaseProjectToSrs } from "@/server/project-route-handlers";

type Params = { params: Promise<{ projectId: string; projectSuffix: string }> };

export async function POST(_request: Request, { params }: Params) {
  const { projectId, projectSuffix } = await params;
  return releaseProjectToSrs(joinedProjectId(projectId, projectSuffix));
}
