import { NextResponse } from "next/server";
import { decodedRouteParam } from "@/lib/route-ids";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

type Params = { params: Promise<{ meetingId: string }> };

export async function POST(request: Request, { params }: Params) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const { meetingId } = await params;
    const meeting = decodedRouteParam(meetingId);
    const payload = await request.json().catch(() => ({}));
    const data = await frappeCall("bedo_platform.api.web.confirm_case3_handover_meeting", { meeting, payload }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Meeting attendance could not be confirmed.");
  }
}
