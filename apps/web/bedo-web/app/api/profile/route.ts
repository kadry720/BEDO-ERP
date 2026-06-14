import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function PATCH(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    const result = await frappeCall("bedo_platform.api.web.update_my_profile", { payload }, session.user);
    return NextResponse.json(result);
  } catch (error) {
    return apiErrorResponse(error, "Profile could not be updated.");
  }
}
