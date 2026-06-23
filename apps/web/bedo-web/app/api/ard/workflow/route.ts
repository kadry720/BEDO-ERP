import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    const trainer_item = payload.trainer_item;

    if (payload.action === "schedule_internal_sync") {
      await frappeCall("bedo_platform.api.web.schedule_ard_internal_sync_meeting", { trainer_item, payload }, session.user);
    } else if (payload.action === "complete_internal_sync") {
      await frappeCall("bedo_platform.api.web.complete_ard_internal_sync_meeting", { trainer_item }, session.user);
    } else if (payload.action === "assign_owner") {
      await frappeCall("bedo_platform.api.web.assign_ard_project_owner", { trainer_item, project_owner: payload.project_owner }, session.user);
    } else if (payload.action === "select_team") {
      await frappeCall("bedo_platform.api.web.select_ard_team", { trainer_item, users: payload.users || [] }, session.user);
    } else if (payload.action === "progress_review") {
      await frappeCall("bedo_platform.api.web.submit_ard_progress_review_outcome", { trainer_item, payload }, session.user);
    } else if (payload.action === "request_interruption") {
      await frappeCall("bedo_platform.api.web.submit_ard_interruption_request", { trainer_item, payload }, session.user);
    } else if (payload.action === "confirm_procurement") {
      await frappeCall("bedo_platform.api.web.confirm_ard_procurement_items_received", { trainer_item }, session.user);
    } else if (payload.action === "choose_electronics_subcase") {
      await frappeCall("bedo_platform.api.web.choose_ard_electronics_subcase", { trainer_item, payload }, session.user);
    } else if (payload.action === "complete_electronics") {
      await frappeCall("bedo_platform.api.web.complete_ard_electronics_action", { trainer_item }, session.user);
    } else if (payload.action === "complete_concept_proof") {
      await frappeCall("bedo_platform.api.web.complete_ard_concept_proof", { trainer_item }, session.user);
    } else if (payload.action === "submit_scmdp") {
      await frappeCall("bedo_platform.api.web.submit_ard_scmdp", { trainer_item, payload }, session.user);
    } else {
      return NextResponse.json({ error: "Unsupported ARD workflow action." }, { status: 400 });
    }

    const data = await frappeCall("bedo_platform.api.web.get_ard_workspace", { trainer_item }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "ARD workflow action failed.");
  }
}
