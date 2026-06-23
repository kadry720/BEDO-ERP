import { NextResponse } from "next/server";
import { decodedRouteParam } from "@/lib/route-ids";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

type Params = { params: Promise<{ trainerItemId: string }> };

export async function POST(request: Request, { params }: Params) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const { trainerItemId } = await params;
    const trainerItem = decodedRouteParam(trainerItemId);
    const payload = await request.json().catch(() => ({}));
    await frappeCall("bedo_platform.api.web.schedule_case3_handover_meeting", { trainer_item: trainerItem, payload }, session.user);
    const data = await frappeCall("bedo_platform.api.web.get_trainer_item_workspace", { trainer_item: trainerItem }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Case 3 handover meeting could not be scheduled.");
  }
}
