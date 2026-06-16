import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const mutationMethods = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function isLocalOrigin(origin: URL) {
  if (["localhost", "127.0.0.1", "::1"].includes(origin.hostname)) return true;
  if (/^10\./.test(origin.hostname)) return true;
  if (/^192\.168\./.test(origin.hostname)) return true;
  const private172 = origin.hostname.match(/^172\.(\d{1,2})\./);
  return Boolean(private172 && Number(private172[1]) >= 16 && Number(private172[1]) <= 31);
}

function allowedOrigins(request: NextRequest) {
  const configured = [process.env.BEDO_WEB_ALLOWED_ORIGIN, process.env.BEDO_WEB_PUBLIC_URL]
    .filter(Boolean)
    .map((value) => String(value).replace(/\/$/, ""));
  return new Set([request.nextUrl.origin, ...configured]);
}

function requestSourceOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (origin) return origin.replace(/\/$/, "");
  const referer = request.headers.get("referer");
  if (!referer) return "";
  try {
    return new URL(referer).origin;
  } catch {
    return "";
  }
}

function hasNonJsonBody(request: NextRequest) {
  const contentType = request.headers.get("content-type") || "";
  const contentLength = request.headers.get("content-length");
  return Boolean(contentType) && contentLength !== "0" && !contentType.toLowerCase().includes("application/json");
}

export function rejectUnsafeMutation(request: NextRequest) {
  if (!request.nextUrl.pathname.startsWith("/api/")) return null;
  if (!mutationMethods.has(request.method.toUpperCase())) return null;

  const source = requestSourceOrigin(request);
  const allowed = allowedOrigins(request);
  if (source) {
    try {
      const sourceUrl = new URL(source);
      const localDevAllowed = process.env.NODE_ENV !== "production" && isLocalOrigin(sourceUrl);
      if (!allowed.has(source) && !localDevAllowed) {
        return NextResponse.json({ error: "Invalid request origin." }, { status: 403 });
      }
    } catch {
      return NextResponse.json({ error: "Invalid request origin." }, { status: 403 });
    }
  } else if (process.env.NODE_ENV === "production") {
    return NextResponse.json({ error: "Missing request origin." }, { status: 403 });
  }

  if (!request.nextUrl.pathname.startsWith("/api/auth/") && hasNonJsonBody(request)) {
    return NextResponse.json({ error: "JSON content type is required." }, { status: 415 });
  }

  return null;
}
