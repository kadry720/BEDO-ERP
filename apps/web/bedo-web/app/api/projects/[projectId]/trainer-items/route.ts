import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET(_request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const { projectId } = await params;
  const data = await frappeCall("bedo_platform.api.web.list_trainer_items_for_project", { project: projectId }, session.user);
  return NextResponse.json(data);
}

export async function POST(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const { projectId } = await params;
  const payload = await request.json();
  await frappeCall("bedo_platform.api.web.add_trainer_item", { project: projectId, payload }, session.user);
  const data = await frappeCall("bedo_platform.api.web.list_trainer_items_for_project", { project: projectId }, session.user);
  return NextResponse.json(data);
}
