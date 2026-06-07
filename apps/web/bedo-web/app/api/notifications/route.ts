import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const data = await frappeCall("bedo_platform.api.web.list_notifications", { limit: 50 }, session.user);
  return NextResponse.json(data);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const payload = await request.json();
  if (payload.notification) {
    await frappeCall("bedo_platform.api.web.mark_notification_as_read", { notification: payload.notification }, session.user);
  } else {
    await frappeCall("bedo_platform.api.web.mark_all_notifications_as_read", {}, session.user);
  }
  const data = await frappeCall("bedo_platform.api.web.list_notifications", { limit: 50 }, session.user);
  return NextResponse.json(data);
}
