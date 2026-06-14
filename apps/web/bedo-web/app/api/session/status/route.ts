import { NextResponse } from "next/server";
import { getSession } from "@/server/session";
import { sessionStatus } from "@/server/session-registry";

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ valid: false, reason: "not_authenticated" }, { status: 401 });
  const status = sessionStatus(session);
  return NextResponse.json(status, { status: status.valid ? 200 : 401 });
}
