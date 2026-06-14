import { NextResponse } from "next/server";
import { decodedRouteParam } from "@/lib/route-ids";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

type Params = { params: Promise<{ trainerItemId: string }> };

export async function POST(_request: Request, { params }: Params) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const { trainerItemId } = await params;
    const trainerItem = decodedRouteParam(trainerItemId);
    await frappeCall("bedo_platform.api.web.complete_command_center_case_1", { trainer_item: trainerItem }, session.user);
    const data = await frappeCall("bedo_platform.api.web.get_trainer_item_workspace", { trainer_item: trainerItem }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Command Center handoff could not be completed.");
  }
}
