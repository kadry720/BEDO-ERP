import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const data = await frappeCall("bedo_platform.api.web.list_eligible_project_owners", {}, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Project owners could not be loaded.");
  }
}
