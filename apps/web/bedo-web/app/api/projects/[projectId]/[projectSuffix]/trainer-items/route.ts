import { addTrainerItem, joinedProjectId, listTrainerItems } from "@/server/project-route-handlers";

type Params = { params: Promise<{ projectId: string; projectSuffix: string }> };

export async function GET(_request: Request, { params }: Params) {
  const { projectId, projectSuffix } = await params;
  return listTrainerItems(joinedProjectId(projectId, projectSuffix));
}

export async function POST(request: Request, { params }: Params) {
  const { projectId, projectSuffix } = await params;
  return addTrainerItem(request, joinedProjectId(projectId, projectSuffix));
}
