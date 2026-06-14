import { NextResponse } from "next/server";
import { FrappeRequestError } from "@/server/frappe";

export function apiErrorResponse(error: unknown, fallback = "Request failed.") {
  if (error instanceof FrappeRequestError) {
    return NextResponse.json({ error: error.message || fallback }, { status: error.status });
  }
  if (error instanceof SyntaxError) {
    return NextResponse.json({ error: "Invalid JSON payload." }, { status: 400 });
  }
  return NextResponse.json({ error: fallback }, { status: 500 });
}

export async function withApiErrors(callback: () => Promise<Response | NextResponse>, fallback?: string) {
  try {
    return await callback();
  } catch (error) {
    return apiErrorResponse(error, fallback);
  }
}
