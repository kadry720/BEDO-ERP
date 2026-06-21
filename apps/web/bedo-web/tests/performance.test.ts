import assert from "node:assert/strict";
import test from "node:test";
import { logPerformanceEvent, userFingerprint, withPerformanceLog } from "../server/performance";

test("performance logs are structured and do not expose raw users", () => {
  const previousEnv = process.env.BEDO_PERFORMANCE_LOGS;
  process.env.BEDO_PERFORMANCE_LOGS = "1";
  const lines: string[] = [];
  const originalInfo = console.info;
  console.info = (message?: unknown) => {
    lines.push(String(message));
  };

  try {
    logPerformanceEvent({
      layer: "next-frappe",
      route_or_method: "bedo_platform.api.web.me",
      request_id: "request-1",
      status: "ok",
      duration_ms: 42,
      user: "gm@example.local",
    });
  } finally {
    console.info = originalInfo;
    restoreEnv("BEDO_PERFORMANCE_LOGS", previousEnv);
  }

  assert.equal(lines.length, 1);
  const payload = JSON.parse(lines[0]);
  assert.equal(payload.event, "bedo.performance");
  assert.equal(payload.layer, "next-frappe");
  assert.equal(payload.route_or_method, "bedo_platform.api.web.me");
  assert.equal(payload.request_id, "request-1");
  assert.equal(payload.status, "ok");
  assert.equal(payload.duration_ms, 42);
  assert.equal(typeof payload.user_hash, "string");
  assert.ok(!lines[0].includes("gm@example.local"));
});

test("withPerformanceLog logs failures before rethrowing", async () => {
  const previousEnv = process.env.BEDO_PERFORMANCE_LOGS;
  process.env.BEDO_PERFORMANCE_LOGS = "1";
  const lines: string[] = [];
  const originalInfo = console.info;
  console.info = (message?: unknown) => {
    lines.push(String(message));
  };

  try {
    await assert.rejects(
      () =>
        withPerformanceLog(
          {
            layer: "next-session",
            route_or_method: "/api/session/status",
            request_id: "request-2",
            user: "gm@example.local",
          },
          async () => {
            throw new Error("redis unavailable");
          }
        ),
      /redis unavailable/
    );
  } finally {
    console.info = originalInfo;
    restoreEnv("BEDO_PERFORMANCE_LOGS", previousEnv);
  }

  assert.equal(JSON.parse(lines[0]).status, "error");
});

test("user fingerprints are stable but not reversible from the raw value", () => {
  assert.equal(userFingerprint("gm@example.local"), userFingerprint("gm@example.local"));
  assert.notEqual(userFingerprint("gm@example.local"), "gm@example.local");
});

function restoreEnv(name: string, value: string | undefined) {
  if (value === undefined) {
    delete process.env[name];
  } else {
    process.env[name] = value;
  }
}
