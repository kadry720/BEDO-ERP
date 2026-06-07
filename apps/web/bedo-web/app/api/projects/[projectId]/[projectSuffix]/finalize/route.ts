import { finalizeProjectDetails, joinedProjectId } from "@/server/project-route-handlers";

type Params = { params: Promise<{ projectId: string; projectSuffix: string }> };

export async function POST(_request: Request, { params }: Params) {
  const { projectId, projectSuffix } = await params;
  return finalizeProjectDetails(joinedProjectId(projectId, projectSuffix));
}
