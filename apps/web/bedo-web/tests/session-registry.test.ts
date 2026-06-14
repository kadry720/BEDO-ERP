import assert from "node:assert/strict";
import test from "node:test";
import type { BedoUserContext } from "../lib/routes";
import {
  __resetSessionRegistryForTests,
  activateSession,
  allowLoginChallenge,
  createLoginChallenge,
  denyLoginChallenge,
  getActiveSession,
  getLoginChallenge,
  sessionStatus,
} from "../server/session-registry";

process.env.BEDO_ENV = "test";
process.env.BEDO_DISABLE_SESSION_REDIS = "1";

function context(sessionId: string): BedoUserContext {
  return {
    user: "gm@example.local",
    username: "gm",
    first_name: "General",
    middle_name: "",
    last_name: "Manager",
    enabled: 1,
    roles: ["BEDO Employee", "General Manager"],
    landing_route: "/gm",
    modules: [],
    session_id: sessionId,
  };
}

test("active session validates and refreshes", async () => {
  __resetSessionRegistryForTests();
  await activateSession("gm@example.local", "session-1");

  assert.deepEqual(await sessionStatus(context("session-1")), { valid: true, conflict: null });
  assert.equal((await getActiveSession("gm@example.local"))?.sessionId, "session-1");
});

test("allow challenge transfers the active session", async () => {
  __resetSessionRegistryForTests();
  await activateSession("gm@example.local", "session-1");
  const challenge = await createLoginChallenge(context("session-1"), "session-2", "challenge-1");

  assert.equal((await getLoginChallenge(challenge.challengeId))?.status, "pending");
  assert.equal(await allowLoginChallenge(challenge.challengeId, context("session-1")), true);
  assert.equal((await getActiveSession("gm@example.local"))?.sessionId, "session-2");
  assert.deepEqual(await sessionStatus(context("session-1")), { valid: false, reason: "replaced_session" });
});

test("deny challenge keeps the original active session", async () => {
  __resetSessionRegistryForTests();
  await activateSession("gm@example.local", "session-1");
  const challenge = await createLoginChallenge(context("session-1"), "session-2", "challenge-2");

  assert.equal(await denyLoginChallenge(challenge.challengeId, context("session-1")), true);
  assert.equal((await getActiveSession("gm@example.local"))?.sessionId, "session-1");
  assert.equal((await getLoginChallenge(challenge.challengeId))?.status, "denied");
});
