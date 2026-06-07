import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function POST(_request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const { projectId } = await params;
  await frappeCall("bedo_platform.api.web.release_project_to_srs", { project: projectId }, session.user);
  const project = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  const items = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.list_trainer_items_for_project", { project: projectId }, session.user);
  return NextResponse.json({ ...project, ...items });
}
