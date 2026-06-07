import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const payload = await request.json();
  const trainer_item = payload.trainer_item;
  try {
    if (payload.action === "assign_owner") {
      await frappeCall("bedo_platform.api.web.assign_srs_project_owner", { trainer_item, project_owner: payload.project_owner }, session.user);
    } else if (payload.action === "submit_coordination") {
      await frappeCall("bedo_platform.api.web.submit_mandatory_coordination", { trainer_item, payload }, session.user);
    } else if (payload.action === "submit_bmdp") {
      await frappeCall("bedo_platform.api.web.submit_srs_bmdp_path", { trainer_item, bmdp_path: payload.bmdp_path }, session.user);
    } else {
      return NextResponse.json({ error: "Unsupported workflow action." }, { status: 400 });
    }
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Workflow action failed." }, { status: 400 });
  }
  const data = await frappeCall("bedo_platform.api.web.get_trainer_item_workspace", { trainer_item }, session.user);
  return NextResponse.json(data);
}
