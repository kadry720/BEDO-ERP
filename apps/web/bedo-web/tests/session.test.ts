import assert from "node:assert/strict";
import test from "node:test";
import type { BedoUserContext } from "../lib/routes";
import { signSession, verifySessionToken } from "../server/session";

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
  modules: [],
  session_id: "session-1",
};

test("valid session token verifies", () => {
  const token = signSession(context);

  assert.equal(verifySessionToken(token)?.user, context.user);
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
