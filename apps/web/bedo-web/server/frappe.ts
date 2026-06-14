import crypto from "crypto";
import { randomUUID } from "crypto";
import { requireConfiguredSecret } from "@/server/config";
import { hmacSha256, randomNonce } from "@/server/crypto";

type FrappeResponse<T> = {
  message?: T;
  exc?: string;
  exception?: string;
  _server_messages?: string;
};

export class FrappeRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "FrappeRequestError";
    this.status = status;
  }
}

function frappeUrl() {
  return (process.env.FRAPPE_INTERNAL_URL || "http://localhost:8000").replace(/\/$/, "");
}

function serviceSecret() {
  return requireConfiguredSecret("BEDO_WEB_SERVICE_SECRET");
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
    "X-BEDO-Request-ID": randomUUID(),
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
    const rawMessage = extractFrappeMessage(data);
    throw new FrappeRequestError(cleanFrappeMessage(rawMessage), inferFrappeStatus(rawMessage, response.status));
  }
  return data.message as T;
}

function extractFrappeMessage<T>(data: FrappeResponse<T>) {
  if (data.exception) return data.exception;
  if (data.exc) return data.exc;
  if (!data._server_messages) return "Frappe request failed.";
  try {
    const messages = JSON.parse(data._server_messages);
    const first = Array.isArray(messages) ? messages[0] : messages;
    const parsed = typeof first === "string" ? JSON.parse(first) : first;
    return parsed.message || parsed.title || String(first);
  } catch {
    return data._server_messages;
  }
}

function cleanFrappeMessage(rawMessage: string) {
  const firstLine = String(rawMessage || "Frappe request failed.").split("\n")[0] || "Frappe request failed.";
  return firstLine
    .replace(/^frappe\.exceptions\.[A-Za-z]+:\s*/, "")
    .replace(/^ValueError:\s*/, "")
    .replace(/^ValidationError:\s*/, "")
    .replace(/^MandatoryError:\s*/, "")
    .trim();
}

function inferFrappeStatus(rawMessage: string, responseStatus: number) {
  if ([401, 403, 404].includes(responseStatus)) return responseStatus;
  if (/PermissionError|not authorized|do not have access|access is required|not permitted/i.test(rawMessage)) return 403;
  if (/DoesNotExistError|not found|does not exist/i.test(rawMessage)) return 404;
  if (/ValueError|ValidationError|MandatoryError|required|invalid|valid value|already|not available|not the active/i.test(rawMessage)) return 400;
  if (responseStatus >= 400 && responseStatus < 500) return responseStatus;
  return 500;
}
