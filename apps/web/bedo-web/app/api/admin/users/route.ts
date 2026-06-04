import { NextResponse } from "next/server";
import type { AdminUser } from "@/features/admin/types";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const data = await frappeCall<{ users: AdminUser[] }>("bedo_platform.api.web.list_users", {}, session.user);
  return NextResponse.json(data);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const payload = await request.json();
  await frappeCall("bedo_platform.api.web.create_user", { payload }, session.user);
  const data = await frappeCall<{ users: AdminUser[] }>("bedo_platform.api.web.list_users", {}, session.user);
  return NextResponse.json(data);
}

export async function PATCH(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const payload = await request.json();
  await frappeCall("bedo_platform.api.web.set_user_enabled", {
    target_user: payload.user,
    enabled: payload.enabled
  }, session.user);
  return NextResponse.json({ success: true });
}
