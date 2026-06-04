import crypto from "crypto";

export function base64url(input: Buffer | string) {
  return Buffer.from(input).toString("base64url");
}

export function fromBase64url(input: string) {
  return Buffer.from(input, "base64url").toString("utf8");
}

export function hmacSha256(secret: string, payload: string) {
  return crypto.createHmac("sha256", secret).update(payload).digest("hex");
}

export function randomNonce() {
  return crypto.randomBytes(16).toString("hex");
}
