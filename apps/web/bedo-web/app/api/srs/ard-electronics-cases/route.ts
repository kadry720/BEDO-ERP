import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

const electronicsCapabilityRole = "SRS Electronics Section Head";

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    if (!session.roles.includes(electronicsCapabilityRole)) {
      return NextResponse.json({ error: "SRS Electronics Section Head access is required." }, { status: 403 });
    }
    const cases = await frappeCall("bedo_platform.api.web.list_srs_electronics_ard_cases", {}, session.user);
    return NextResponse.json({ cases });
  } catch (error) {
    return apiErrorResponse(error, "Electronics cases request failed.");
  }
}
