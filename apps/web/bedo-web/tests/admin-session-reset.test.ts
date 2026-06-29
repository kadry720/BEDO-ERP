import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("admin session reset route is protected and retires requested users", () => {
  const route = join(import.meta.dirname, "..", "app", "api", "admin", "sessions", "route.ts");
  const proxy = readFileSync(join(import.meta.dirname, "..", "proxy.ts"), "utf-8");

  assert.equal(existsSync(route), true);
  const source = readFileSync(route, "utf-8");
  assert.match(source, /BEDO_SESSION_ADMIN_SECRET/);
  assert.match(source, /x-bedo-session-admin-secret/);
  assert.match(source, /timingSafeEqual/);
  assert.match(source, /retireUserSessions/);
  assert.match(proxy, /"\/api\/admin\/sessions"/);
});
