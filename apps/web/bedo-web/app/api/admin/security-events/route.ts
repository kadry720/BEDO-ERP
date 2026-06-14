import { NextResponse } from "next/server";
import type { SecurityEvent } from "@/features/admin/types";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const filters = await request.json().catch(() => ({}));
    const data = await frappeCall<{ events: SecurityEvent[]; page: number; page_size: number; total: number }>(
      "bedo_platform.api.web.list_security_events",
      { filters },
      session.user
    );
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Security events could not be loaded.");
  }
}
