import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const data = await frappeCall("bedo_platform.api.web.list_notifications", { limit: 50 }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Notifications could not be loaded.");
  }
}

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    const action = payload.action || (payload.notification ? "mark_read" : "mark_all_read");
    if (action === "mark_read" && payload.notification) {
      await frappeCall("bedo_platform.api.web.mark_notification_as_read", { notification: payload.notification }, session.user);
    } else if (action === "mark_unread" && payload.notification) {
      await frappeCall("bedo_platform.api.web.mark_notification_as_unread", { notification: payload.notification }, session.user);
    } else if (action === "mark_all_read") {
      await frappeCall("bedo_platform.api.web.mark_all_notifications_as_read", {}, session.user);
    } else {
      return NextResponse.json({ error: "Unsupported notification action." }, { status: 400 });
    }
    const data = await frappeCall("bedo_platform.api.web.list_notifications", { limit: 50 }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Notification could not be updated.");
  }
}
