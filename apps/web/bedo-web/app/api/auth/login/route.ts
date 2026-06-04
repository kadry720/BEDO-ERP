import { NextResponse } from "next/server";
import { redirect } from "next/navigation";
import type { BedoUserContext } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { setSession } from "@/server/session";

type LoginResponse = {
  success: boolean;
  message?: string;
  context?: BedoUserContext;
};

export async function POST(request: Request) {
  const contentType = request.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const body = isJson
    ? await request.json().catch(() => ({}))
    : Object.fromEntries((await request.formData()).entries());
  const username = String(body.username || "");
  const password = String(body.password || "");
  const result = await frappeCall<LoginResponse>("bedo_platform.api.web.login", { username, password });
  if (!result.success || !result.context) {
    if (!isJson) redirect("/login?error=invalid");
    return NextResponse.json({ error: "Invalid username or password." }, { status: 401 });
  }
  await setSession(result.context);
  if (!isJson) redirect(result.context.landing_route || "/access-not-configured");
  return NextResponse.json({ route: result.context.landing_route || "/access-not-configured" });
}
