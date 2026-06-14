import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import crypto from "crypto";
import type { BedoUserContext } from "@/lib/routes";
import { requireConfiguredSecret } from "@/server/config";
import { base64url, fromBase64url, hmacSha256 } from "@/server/crypto";

const cookieName = "bedo_session";
const maxAgeSeconds = 60 * 60 * 8;

type SessionEnvelope = {
  context: BedoUserContext;
  exp: number;
};

function minimalContext(context: BedoUserContext): BedoUserContext {
  return {
    user: context.user,
    username: context.username,
    first_name: context.first_name,
    middle_name: context.middle_name || "",
    last_name: context.last_name,
    enabled: context.enabled,
    roles: context.roles,
    landing_route: context.landing_route,
    modules: [],
    session_id: context.session_id
  };
}

function sessionSecret() {
  return requireConfiguredSecret("BEDO_WEB_SESSION_SECRET");
}

function timingSafeEqualHex(left: string, right: string) {
  try {
    const leftBuffer = Buffer.from(left, "hex");
    const rightBuffer = Buffer.from(right, "hex");
    return leftBuffer.length === rightBuffer.length && crypto.timingSafeEqual(leftBuffer, rightBuffer);
  } catch {
    return false;
  }
}

export function signSession(context: BedoUserContext) {
  const envelope: SessionEnvelope = {
    context: minimalContext(context),
    exp: Math.floor(Date.now() / 1000) + maxAgeSeconds
  };
  const payload = base64url(JSON.stringify(envelope));
  const signature = hmacSha256(sessionSecret(), payload);
  return `${payload}.${signature}`;
}

export function verifySessionToken(token?: string): BedoUserContext | null {
  try {
    if (!token || !token.includes(".")) return null;
    const parts = token.split(".");
    if (parts.length !== 2) return null;
    const [payload, signature] = parts;
    if (!payload || !signature) return null;
    const expected = hmacSha256(sessionSecret(), payload);
    if (!timingSafeEqualHex(signature, expected)) return null;
    const envelope = JSON.parse(fromBase64url(payload)) as SessionEnvelope;
    if (!envelope?.exp || envelope.exp < Math.floor(Date.now() / 1000)) return null;
    if (!envelope.context?.user || !envelope.context?.session_id) return null;
    return envelope.context;
  } catch {
    return null;
  }
}

export async function setSession(context: BedoUserContext) {
  const cookieStore = await cookies();
  cookieStore.set(cookieName, signSession(context), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: maxAgeSeconds
  });
}

export async function clearSession() {
  const cookieStore = await cookies();
  cookieStore.delete(cookieName);
}

export async function getSession() {
  const cookieStore = await cookies();
  return verifySessionToken(cookieStore.get(cookieName)?.value);
}

export async function requireSession() {
  const session = await getSession();
  if (!session) redirect("/login");
  return session;
}
