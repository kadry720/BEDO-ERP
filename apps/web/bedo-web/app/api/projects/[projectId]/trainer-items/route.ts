import { addTrainerItem, listTrainerItems } from "@/server/project-route-handlers";

export async function GET(_request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return listTrainerItems(projectId);
}

export async function POST(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return addTrainerItem(request, projectId);
}
