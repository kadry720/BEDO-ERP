import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";

export async function GET() {
  const startedAt = Date.now();
  try {
    const frappe = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.health");
    return NextResponse.json({
      status: "ok",
      app: "bedo-web",
      frappe,
      latency_ms: Date.now() - startedAt,
    });
  } catch {
    return NextResponse.json(
      {
        status: "degraded",
        app: "bedo-web",
        frappe: "unavailable",
        latency_ms: Date.now() - startedAt,
      },
      { status: 503 }
    );
  }
}
