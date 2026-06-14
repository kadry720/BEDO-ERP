import { NextResponse } from "next/server";
import { redirect } from "next/navigation";
import { randomUUID } from "crypto";
import type { BedoUserContext } from "@/lib/routes";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { setSession } from "@/server/session";
import { activateSession, createLoginChallenge, getActiveSession } from "@/server/session-registry";

type LoginResponse = {
  success: boolean;
  message?: string;
  context?: BedoUserContext;
};

export async function POST(request: Request) {
  try {
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
    const sessionId = randomUUID();
    const activeSession = await getActiveSession(result.context.user);
    if (activeSession) {
      const challenge = await createLoginChallenge(result.context, sessionId, randomUUID());
      if (!isJson) redirect("/login?error=already_signed_in");
      return NextResponse.json(
        {
          error: "This account is already signed in.",
          conflict: true,
          challengeId: challenge.challengeId,
        },
        { status: 409 }
      );
    }
    const context = { ...result.context, session_id: sessionId };
    await activateSession(context.user, sessionId);
    await setSession(context);
    if (!isJson) redirect(context.landing_route || "/access-not-configured");
    return NextResponse.json({ route: context.landing_route || "/access-not-configured" });
  } catch (error) {
    const contentType = request.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      redirect("/login?error=invalid");
    }
    return apiErrorResponse(error, "Login failed.");
  }
}
