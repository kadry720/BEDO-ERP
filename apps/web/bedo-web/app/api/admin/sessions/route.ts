import { createHash, timingSafeEqual } from "crypto";
import { NextResponse } from "next/server";
import { retireUserSessions } from "@/server/session-registry";

const adminSecretHeader = "x-bedo-session-admin-secret";

function hashSecret(value: string) {
  return createHash("sha256").update(value).digest();
}

function hasValidAdminSecret(request: Request) {
  const configured = process.env.BEDO_SESSION_ADMIN_SECRET || "";
  const supplied = request.headers.get(adminSecretHeader) || "";
  if (!configured || !supplied) return false;
  return timingSafeEqual(hashSecret(configured), hashSecret(supplied));
}

function requestedUsers(payload: Record<string, unknown>) {
  const rawUsers = Array.isArray(payload.users) ? payload.users : [payload.user];
  return Array.from(
    new Set(
      rawUsers
        .map((user) => String(user || "").trim())
        .filter(Boolean)
        .slice(0, 25)
    )
  );
}

export async function POST(request: Request) {
  if (!hasValidAdminSecret(request)) {
    return NextResponse.json({ error: "Forbidden." }, { status: 403 });
  }

  const payload = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const users = requestedUsers(payload);
  if (!users.length) {
    return NextResponse.json({ error: "At least one user is required." }, { status: 400 });
  }

  for (const user of users) {
    await retireUserSessions(user);
  }

  return NextResponse.json({ success: true, users, count: users.length });
}
