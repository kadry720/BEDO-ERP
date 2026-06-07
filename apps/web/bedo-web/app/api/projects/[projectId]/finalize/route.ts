import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function POST(_request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const { projectId } = await params;
  await frappeCall("bedo_platform.api.web.finalize_project_details", { project: projectId }, session.user);
  const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  return NextResponse.json(data);
}
