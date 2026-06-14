import { finalizeProjectDetails } from "@/server/project-route-handlers";

export async function POST(_request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return finalizeProjectDetails(projectId);
}
