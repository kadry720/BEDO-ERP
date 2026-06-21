import { randomUUID } from "crypto";
import { NextResponse } from "next/server";
import { withPerformanceLog } from "@/server/performance";
import { getSession } from "@/server/session";
import { sessionStatus } from "@/server/session-registry";

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ valid: false, reason: "not_authenticated" }, { status: 401 });
  const status = await withPerformanceLog(
    {
      layer: "next-session",
      route_or_method: "/api/session/status",
      request_id: randomUUID(),
      user: session.user,
    },
    () => sessionStatus(session)
  );
  return NextResponse.json(status, { status: status.valid ? 200 : 401 });
}
