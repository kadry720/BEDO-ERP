import { NextResponse } from "next/server";
import type { AdminUser } from "@/features/admin/types";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const data = await frappeCall<{ users: AdminUser[] }>("bedo_platform.api.web.list_users", {}, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Users could not be loaded.");
  }
}

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    await frappeCall("bedo_platform.api.web.create_user", { payload }, session.user);
    const data = await frappeCall<{ users: AdminUser[] }>("bedo_platform.api.web.list_users", {}, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "User could not be created.");
  }
}

export async function PATCH(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    await frappeCall("bedo_platform.api.web.update_user", {
      target_user: payload.user,
      payload
    }, session.user);
    const data = await frappeCall<{ users: AdminUser[] }>("bedo_platform.api.web.list_users", {}, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "User could not be updated.");
  }
}

export async function DELETE(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    await frappeCall("bedo_platform.api.web.delete_user", {
      target_user: payload.user
    }, session.user);
    const data = await frappeCall<{ users: AdminUser[] }>("bedo_platform.api.web.list_users", {}, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "User could not be deleted.");
  }
}
