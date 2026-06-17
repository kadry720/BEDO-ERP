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
  retireSession,
  retireUserSessions,
  sessionStatus,
} from "../server/session-registry";

process.env.BEDO_ENV = "test";
process.env.BEDO_DISABLE_SESSION_REDIS = "1";

function restoreEnv(name: string, value: string | undefined) {
  if (value === undefined) {
    delete process.env[name];
  } else {
    process.env[name] = value;
  }
}

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

test("stale cookie after logout does not reactivate the retired session", async () => {
  __resetSessionRegistryForTests();
  await activateSession("gm@example.local", "session-1");

  await retireSession("gm@example.local", "session-1");

  assert.equal(await getActiveSession("gm@example.local"), null);
  assert.deepEqual(await sessionStatus(context("session-1")), { valid: false, reason: "retired_session" });
});

test("retiring the active session clears pending login challenges", async () => {
  __resetSessionRegistryForTests();
  await activateSession("gm@example.local", "session-1");
  const challenge = await createLoginChallenge(context("session-1"), "session-2", "challenge-3");

  await retireSession("gm@example.local", "session-1");

  assert.equal(await getLoginChallenge(challenge.challengeId), null);
});

test("login after explicit logout can activate a fresh session", async () => {
  __resetSessionRegistryForTests();
  await activateSession("gm@example.local", "session-1");
  await retireSession("gm@example.local", "session-1");

  await activateSession("gm@example.local", "session-2");

  assert.deepEqual(await sessionStatus(context("session-2")), { valid: true, conflict: null });
});

test("retireUserSessions clears active state for forced logout", async () => {
  __resetSessionRegistryForTests();
  await activateSession("gm@example.local", "session-1");

  await retireUserSessions("gm@example.local");

  assert.equal(await getActiveSession("gm@example.local"), null);
  assert.deepEqual(await sessionStatus(context("session-1")), { valid: false, reason: "retired_session" });
});

test("production session registry rejects memory fallback", async () => {
  __resetSessionRegistryForTests();
  const previous = {
    BEDO_ENV: process.env.BEDO_ENV,
    BEDO_DISABLE_SESSION_REDIS: process.env.BEDO_DISABLE_SESSION_REDIS,
    BEDO_SESSION_REDIS_URL: process.env.BEDO_SESSION_REDIS_URL,
    REDIS_CACHE_URL: process.env.REDIS_CACHE_URL,
  };
  process.env.BEDO_ENV = "production";
  process.env.BEDO_DISABLE_SESSION_REDIS = "1";
  delete process.env.BEDO_SESSION_REDIS_URL;
  delete process.env.REDIS_CACHE_URL;

  await assert.rejects(
    () => activateSession("gm@example.local", "session-production"),
    /BEDO session Redis is required/
  );

  restoreEnv("BEDO_ENV", previous.BEDO_ENV);
  restoreEnv("BEDO_DISABLE_SESSION_REDIS", previous.BEDO_DISABLE_SESSION_REDIS);
  restoreEnv("BEDO_SESSION_REDIS_URL", previous.BEDO_SESSION_REDIS_URL);
  restoreEnv("REDIS_CACHE_URL", previous.REDIS_CACHE_URL);
  __resetSessionRegistryForTests();
});
