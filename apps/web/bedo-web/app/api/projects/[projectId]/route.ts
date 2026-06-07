import { deleteProject, getProject, updateProject } from "@/server/project-route-handlers";

type Params = { params: Promise<{ projectId: string }> };

export async function GET(_request: Request, { params }: Params) {
  const { projectId } = await params;
  return getProject(projectId);
}

export async function PATCH(request: Request, { params }: Params) {
  const { projectId } = await params;
  return updateProject(request, projectId);
}

export async function DELETE(_request: Request, { params }: Params) {
  const { projectId } = await params;
  return deleteProject(projectId);
}
