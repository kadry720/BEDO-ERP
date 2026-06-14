import { NextResponse } from "next/server";
import { activateSession, consumeLoginChallenge, getLoginChallenge } from "@/server/session-registry";
import { setSession } from "@/server/session";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const challengeId = searchParams.get("challengeId") || "";
  const challenge = challengeId ? await getLoginChallenge(challengeId) : null;
  if (!challenge) return NextResponse.json({ error: "Login request expired." }, { status: 410 });
  if (challenge.status === "pending") return NextResponse.json({ status: "pending" }, { status: 202 });
  if (challenge.status === "denied") {
    await consumeLoginChallenge(challengeId);
    return NextResponse.json({ error: "This account is already signed in." }, { status: 403 });
  }
  await activateSession(challenge.user, challenge.requestedSessionId);
  await setSession(challenge.context);
  await consumeLoginChallenge(challengeId);
  return NextResponse.json({ route: challenge.context.landing_route || "/access-not-configured" });
}
