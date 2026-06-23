import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json().catch(() => ({}));
    const trainerItem = String(payload.trainer_item || payload.trainerItem || "");
    const result = await frappeCall<{ trainer_item?: string }>("bedo_platform.api.web.execute_workflow_reset", { trainer_item: trainerItem, payload }, session.user);
    if (result.trainer_item) {
      const workspace = await frappeCall("bedo_platform.api.web.get_trainer_item_workspace", { trainer_item: result.trainer_item }, session.user);
      return NextResponse.json(workspace);
    }
    return NextResponse.json(result);
  } catch (error) {
    return apiErrorResponse(error, "Workflow reset could not be completed.");
  }
}
