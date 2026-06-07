import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const url = new URL(request.url);
  const page = Number(url.searchParams.get("page") || 1);
  const page_size = Number(url.searchParams.get("page_size") || 25);
  const data = await frappeCall("bedo_platform.api.web.list_projects_for_user", { page, page_size }, session.user);
  return NextResponse.json(data);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const payload = await request.json();
  const data = await frappeCall("bedo_platform.api.web.create_project", { payload }, session.user);
  return NextResponse.json(data);
}
