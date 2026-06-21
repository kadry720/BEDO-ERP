import crypto from "crypto";
import { isLocalMode } from "@/server/config";

type PerformanceLogInput = {
  layer: string;
  route_or_method: string;
  request_id?: string;
  status: "ok" | "error";
  duration_ms: number;
  user?: string;
};

type TimedOperationInput = Omit<PerformanceLogInput, "status" | "duration_ms">;

export function userFingerprint(user = "") {
  if (!user) return "";
  return crypto.createHash("sha256").update(user).digest("hex").slice(0, 16);
}

export function logPerformanceEvent(input: PerformanceLogInput) {
  if (!shouldLogPerformance()) return;
  const payload: Record<string, string | number> = {
    event: "bedo.performance",
    layer: input.layer,
    route_or_method: input.route_or_method,
    status: input.status,
    duration_ms: Math.max(0, Math.round(input.duration_ms)),
  };
  if (input.request_id) payload.request_id = input.request_id;
  const user_hash = userFingerprint(input.user);
  if (user_hash) payload.user_hash = user_hash;
  console.info(JSON.stringify(payload));
}

export async function withPerformanceLog<T>(input: TimedOperationInput, operation: () => Promise<T>): Promise<T> {
  const startedAt = Date.now();
  try {
    const result = await operation();
    logPerformanceEvent({ ...input, status: "ok", duration_ms: Date.now() - startedAt });
    return result;
  } catch (error) {
    logPerformanceEvent({ ...input, status: "error", duration_ms: Date.now() - startedAt });
    throw error;
  }
}

function shouldLogPerformance() {
  const setting = process.env.BEDO_PERFORMANCE_LOGS;
  if (setting === "0" || setting?.toLowerCase() === "false") return false;
  if (setting === "1" || setting?.toLowerCase() === "true") return true;
  return !isLocalMode();
}
