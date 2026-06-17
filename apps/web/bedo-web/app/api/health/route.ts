import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";

export async function GET() {
  const startedAt = Date.now();
  const timestamp = new Date().toISOString();
  try {
    const frappe = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.health");
    return NextResponse.json({
      status: "ok",
      app: "bedo-web",
      timestamp,
      frappe,
      latency_ms: Date.now() - startedAt,
    });
  } catch {
    return NextResponse.json(
      {
        status: "degraded",
        app: "bedo-web",
        timestamp,
        frappe: "unavailable",
        latency_ms: Date.now() - startedAt,
      },
      { status: 503 }
    );
  }
}
