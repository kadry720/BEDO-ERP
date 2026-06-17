import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { expireSessionCookie, getSession } from "@/server/session";
import { retireSession } from "@/server/session-registry";

export function logoutRedirectUrl(request: Request) {
  const requestUrl = new URL(request.url);
  const forwardedProto = request.headers.get("x-forwarded-proto")?.split(",")[0]?.trim();
  const forwardedHost = request.headers.get("x-forwarded-host")?.split(",")[0]?.trim();
  const host = forwardedHost || request.headers.get("host") || requestUrl.host;
  const protocol = forwardedProto || requestUrl.protocol.replace(":", "") || "http";
  const usableHost = host && !host.startsWith("0.0.0.0") ? host : "";
  if (usableHost) return new URL(`/login`, `${protocol}://${usableHost}`);
  return new URL("/login", process.env.BEDO_WEB_PUBLIC_URL || "http://localhost:3000");
}

export async function POST(request: Request) {
  const session = await getSession();
  if (session) {
    await frappeCall("bedo_platform.api.web.logout", {}, session.user).catch(() => null);
    await retireSession(session.user, session.session_id);
  }
  const response = NextResponse.redirect(logoutRedirectUrl(request), { status: 303 });
  expireSessionCookie(response);
  return response;
}
