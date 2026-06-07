import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const url = new URL(request.url);
  const countOnly = url.searchParams.get("count") === "1";
  if (countOnly) {
    const data = await frappeCall("bedo_platform.api.web.get_pending_approval_count", {}, session.user);
    return NextResponse.json(data);
  }
  const status = url.searchParams.get("status") || "WAITING";
  const data = await frappeCall("bedo_platform.api.web.list_my_pending_approvals", { status }, session.user);
  return NextResponse.json(data);
}
