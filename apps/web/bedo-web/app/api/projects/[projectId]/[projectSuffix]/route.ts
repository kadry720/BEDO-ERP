import { deleteProject, getProject, joinedProjectId, updateProject } from "@/server/project-route-handlers";

type Params = { params: Promise<{ projectId: string; projectSuffix: string }> };

export async function GET(_request: Request, { params }: Params) {
  const { projectId, projectSuffix } = await params;
  return getProject(joinedProjectId(projectId, projectSuffix));
}

export async function PATCH(request: Request, { params }: Params) {
  const { projectId, projectSuffix } = await params;
  return updateProject(request, joinedProjectId(projectId, projectSuffix));
}

export async function DELETE(_request: Request, { params }: Params) {
  const { projectId, projectSuffix } = await params;
  return deleteProject(joinedProjectId(projectId, projectSuffix));
}
