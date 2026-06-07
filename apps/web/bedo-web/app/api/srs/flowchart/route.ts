import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const data = await frappeCall("bedo_platform.api.web.get_srs_flowchart_definition", {}, session.user);
  return NextResponse.json(data);
}
