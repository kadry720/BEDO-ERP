import assert from "node:assert/strict";
import test from "node:test";
import type { BedoUserContext } from "../lib/routes";
import { sessionCookieOptions, signSession, verifySessionToken } from "../server/session";

process.env.BEDO_ENV = "test";
process.env.BEDO_WEB_SESSION_SECRET = "unit-test-session-secret";

const context: BedoUserContext = {
  user: "gm@example.local",
  username: "gm",
  first_name: "General",
  middle_name: "",
  last_name: "Manager",
  enabled: 1,
  roles: ["BEDO Employee", "General Manager"],
  landing_route: "/gm",
  modules: [{ route: "/gm", title: "GM Support Office Dashboard", module: "GM Support Office" }],
  session_id: "session-1",
};

test("valid session token verifies", () => {
  const token = signSession(context);

  assert.equal(verifySessionToken(token)?.user, context.user);
});

test("session token preserves authorized dashboard modules for shell navigation", () => {
  const token = signSession(context);

  assert.deepEqual(verifySessionToken(token)?.modules, context.modules);
});

test("malformed session tokens return null", () => {
  assert.equal(verifySessionToken("bad-token"), null);
  assert.equal(verifySessionToken("bad.payload.signature"), null);
  assert.equal(verifySessionToken(""), null);
});

test("tampered session token returns null", () => {
  const token = signSession(context);
  const [payload, signature] = token.split(".");
  const tampered = `${payload.slice(0, -1)}A.${signature}`;

  assert.equal(verifySessionToken(tampered), null);
});

test("session cookie is not secure for local BEDO_ENV even in production runtime", () => {
  const previousNodeEnv = process.env.NODE_ENV;
  const mutableEnv = process.env as Record<string, string | undefined>;
  process.env.BEDO_ENV = "local";
  mutableEnv.NODE_ENV = "production";

  assert.equal(sessionCookieOptions().secure, false);

  mutableEnv.NODE_ENV = previousNodeEnv;
});
