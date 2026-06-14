import { NextResponse } from "next/server";
import { getSession } from "@/server/session";
import { allowLoginChallenge, denyLoginChallenge } from "@/server/session-registry";

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  const challengeId = String(body.challengeId || "");
  const action = String(body.action || "");
  if (!challengeId || !["allow", "deny"].includes(action)) {
    return NextResponse.json({ error: "Invalid session conflict action." }, { status: 400 });
  }
  const success = action === "allow" ? allowLoginChallenge(challengeId, session) : denyLoginChallenge(challengeId, session);
  if (!success) return NextResponse.json({ error: "Login request is no longer available." }, { status: 404 });
  return NextResponse.json({ success: true, logout: action === "allow" });
}
