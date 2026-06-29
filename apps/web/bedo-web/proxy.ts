import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { rejectUnsafeMutation } from "@/lib/api-guard";

const publicPaths = ["/login", "/api/auth/login", "/api/admin/sessions", "/api/health"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const unsafeMutation = rejectUnsafeMutation(request);
  if (unsafeMutation) return unsafeMutation;
  if (publicPaths.some((path) => pathname === path || pathname.startsWith(`${path}/`))) {
    return NextResponse.next();
  }
  if (pathname.startsWith("/api") && pathname !== "/api/auth/logout") {
    const hasSession = Boolean(request.cookies.get("bedo_session")?.value);
    if (!hasSession) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    return NextResponse.next();
  }
  if (!request.cookies.get("bedo_session")?.value) {
    const login = request.nextUrl.clone();
    login.pathname = "/login";
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"]
};
