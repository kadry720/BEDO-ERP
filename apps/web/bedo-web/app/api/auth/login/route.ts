import { NextResponse } from "next/server";
import type { BedoUserContext } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { setSession } from "@/server/session";

type LoginResponse = {
  success: boolean;
  message?: string;
  context?: BedoUserContext;
};

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const username = String(body.username || "");
  const password = String(body.password || "");
  const result = await frappeCall<LoginResponse>("bedo_platform.api.web.login", { username, password });
  if (!result.success || !result.context) {
    return NextResponse.json({ error: "Invalid username or password." }, { status: 401 });
  }
  await setSession(result.context);
  return NextResponse.json({ route: result.context.landing_route || "/access-not-configured" });
}
