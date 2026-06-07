import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

type Params = { params: Promise<{ projectId: string }> };

export async function GET(_request: Request, { params }: Params) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const { projectId } = await params;
  const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  return NextResponse.json(data);
}

export async function PATCH(request: Request, { params }: Params) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const { projectId } = await params;
  const payload = await request.json();
  await frappeCall("bedo_platform.api.web.update_project_details", { project: projectId, payload }, session.user);
  const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  return NextResponse.json(data);
}

export async function DELETE(_request: Request, { params }: Params) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const { projectId } = await params;
  await frappeCall("bedo_platform.api.web.delete_project", { project: projectId }, session.user);
  return NextResponse.json({ success: true });
}
