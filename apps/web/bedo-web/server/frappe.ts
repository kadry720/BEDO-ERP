import crypto from "crypto";
import { hmacSha256, randomNonce } from "@/server/crypto";

type FrappeResponse<T> = {
  message?: T;
  exc?: string;
  exception?: string;
};

function frappeUrl() {
  return (process.env.FRAPPE_INTERNAL_URL || "http://localhost:8000").replace(/\/$/, "");
}

function serviceSecret() {
  const secret = process.env.BEDO_WEB_SERVICE_SECRET;
  if (!secret) throw new Error("BEDO_WEB_SERVICE_SECRET is not configured.");
  return secret;
}

function serviceHeaders(path: string, body: string, user = "") {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = randomNonce();
  const service = "bedo-web";
  const bodyHash = crypto.createHash("sha256").update(body).digest("hex");
  const payload = [service, user, timestamp, nonce, "POST", path, bodyHash].join("\n");
  return {
    "Content-Type": "application/json",
    "X-BEDO-Service": service,
    "X-BEDO-User": user,
    "X-BEDO-Timestamp": timestamp,
    "X-BEDO-Nonce": nonce,
    "X-BEDO-Signature": hmacSha256(serviceSecret(), payload)
  };
}

export async function frappeCall<T>(method: string, args: Record<string, unknown> = {}, user = ""): Promise<T> {
  const path = `/api/method/${method}`;
  const body = JSON.stringify(args);
  const response = await fetch(`${frappeUrl()}${path}`, {
    method: "POST",
    headers: serviceHeaders(path, body, user),
    body,
    cache: "no-store"
  });
  const data = (await response.json().catch(() => ({}))) as FrappeResponse<T>;
  if (!response.ok || data.exc || data.exception) {
    throw new Error(data.exception || data.exc || "Frappe request failed.");
  }
  return data.message as T;
}
