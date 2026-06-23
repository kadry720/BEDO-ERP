import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const url = new URL(request.url);
    const status = url.searchParams.get("status") || "";
    const data = await frappeCall("bedo_platform.api.web.list_my_meetings", { status }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Meetings could not be loaded.");
  }
}
