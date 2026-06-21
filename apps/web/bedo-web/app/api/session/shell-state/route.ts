import { randomUUID } from "crypto";
import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { withPerformanceLog } from "@/server/performance";
import { getSession } from "@/server/session";
import { loadShellState } from "@/server/shell-state";

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const data = await withPerformanceLog(
      {
        layer: "next-route",
        route_or_method: "/api/session/shell-state",
        request_id: randomUUID(),
        user: session.user,
      },
      () => loadShellState(session.user)
    );
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Shell state could not be loaded.");
  }
}
