import { randomUUID } from "crypto";
import { NextResponse } from "next/server";
import { withPerformanceLog } from "@/server/performance";
import { getSession } from "@/server/session";
import { loadShellState } from "@/server/shell-state";

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const data = await withPerformanceLog(
    {
      layer: "next-route",
      route_or_method: "/api/session/attention",
      request_id: randomUUID(),
      user: session.user,
    },
    () => loadShellState(session.user)
  );
  return NextResponse.json(data);
}
