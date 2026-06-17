import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import type { BedoUserContext } from "@/lib/routes";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession, setSessionCookie } from "@/server/session";
import { activateSession, retireSession } from "@/server/session-registry";

type ProfileUpdateResult = {
  success: boolean;
  profile?: unknown;
  context?: BedoUserContext;
  password_changed?: boolean;
};

export async function PATCH(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    const result = await frappeCall<ProfileUpdateResult>("bedo_platform.api.web.update_my_profile", { payload }, session.user);
    const freshContext = result.context;
    if (!freshContext) return NextResponse.json(result);

    const currentSessionId = session.session_id || randomUUID();
    const nextSessionId = result.password_changed ? randomUUID() : currentSessionId;
    const nextContext = { ...freshContext, session_id: nextSessionId };
    if (result.password_changed || session.user !== nextContext.user) {
      await retireSession(session.user, currentSessionId);
    }
    await activateSession(nextContext.user, nextSessionId);

    const response = NextResponse.json({ ...result, context: nextContext });
    setSessionCookie(response, nextContext);
    return response;
  } catch (error) {
    return apiErrorResponse(error, "Profile could not be updated.");
  }
}
