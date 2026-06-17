import Redis from "ioredis";
import type { BedoUserContext } from "@/lib/routes";
import { isLocalMode, optionalRedisUrl } from "@/server/config";

const activeTtlMs = 8 * 60 * 60 * 1000;
const challengeTtlMs = 2 * 60 * 1000;
const activeTtlSeconds = Math.floor(activeTtlMs / 1000);
const challengeTtlSeconds = Math.floor(challengeTtlMs / 1000);
const retiredTtlSeconds = activeTtlSeconds;

type ActiveSession = {
  user: string;
  sessionId: string;
  lastSeen: number;
  challengeId?: string;
};

export type LoginChallenge = {
  challengeId: string;
  user: string;
  requestedSessionId: string;
  context: BedoUserContext;
  createdAt: number;
  status: "pending" | "allowed" | "denied";
};

type Registry = {
  activeSessions: Map<string, ActiveSession>;
  challenges: Map<string, LoginChallenge>;
  retiredSessions: Map<string, number>;
};

declare global {
  // eslint-disable-next-line no-var
  var __bedoSessionRegistry: Registry | undefined;
}

let redisPromise: Promise<Redis | null> | null = null;

function now() {
  return Date.now();
}

function memoryRegistry() {
  if (!globalThis.__bedoSessionRegistry) {
    globalThis.__bedoSessionRegistry = {
      activeSessions: new Map<string, ActiveSession>(),
      challenges: new Map<string, LoginChallenge>(),
      retiredSessions: new Map<string, number>(),
    };
  }
  cleanupExpiredMemory();
  return globalThis.__bedoSessionRegistry;
}

function cleanupExpiredMemory() {
  const store = globalThis.__bedoSessionRegistry;
  if (!store) return;
  const current = now();
  for (const [user, session] of store.activeSessions.entries()) {
    if (current - session.lastSeen > activeTtlMs) store.activeSessions.delete(user);
  }
  for (const [challengeId, challenge] of store.challenges.entries()) {
    if (current - challenge.createdAt > challengeTtlMs && challenge.status === "pending") {
      store.challenges.delete(challengeId);
      const active = store.activeSessions.get(challenge.user);
      if (active?.challengeId === challengeId) {
        delete active.challengeId;
        store.activeSessions.set(challenge.user, active);
      }
    }
  }
  for (const [key, retiredAt] of store.retiredSessions.entries()) {
    if (current - retiredAt > activeTtlMs) store.retiredSessions.delete(key);
  }
}

function activeKey(user: string) {
  return `bedo:session:active:${user}`;
}

function pendingChallengesKey(user: string) {
  return `bedo:session:pending-challenges:${user}`;
}

function challengeKey(challengeId: string) {
  return `bedo:session:challenge:${challengeId}`;
}

function retiredKey(user: string, sessionId: string) {
  return `bedo:session:retired:${user}:${sessionId}`;
}

function retiredMemoryKey(user: string, sessionId: string) {
  return `${user}:${sessionId}`;
}

async function redis() {
  const url = optionalRedisUrl();
  if (process.env.BEDO_DISABLE_SESSION_REDIS === "1") {
    if (!isLocalMode()) {
      throw new Error("BEDO session Redis is required in production; BEDO_DISABLE_SESSION_REDIS cannot be set.");
    }
    return null;
  }
  if (!url) {
    if (!isLocalMode()) {
      throw new Error("BEDO session Redis is required in production. Set BEDO_SESSION_REDIS_URL.");
    }
    return null;
  }
  if (!redisPromise) {
    redisPromise = (async () => {
      try {
        const client = new Redis(url, {
          lazyConnect: true,
          maxRetriesPerRequest: 1,
          enableOfflineQueue: false,
        });
        await client.connect();
        await client.ping();
        return client;
      } catch (error) {
        if (!isLocalMode()) {
          console.error("BEDO session Redis is unavailable.", error);
          throw new Error("BEDO session Redis is required in production but the connection failed.");
        }
        return null;
      }
    })();
  }
  return redisPromise;
}

async function readJson<T>(key: string) {
  const client = await redis();
  if (!client) return null;
  const raw = await client.get(key).catch(() => null);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    await client.del(key).catch(() => null);
    return null;
  }
}

async function writeJson(key: string, value: unknown, ttlSeconds: number) {
  const client = await redis();
  if (!client) return false;
  try {
    await client.set(key, JSON.stringify(value), "EX", ttlSeconds);
    return true;
  } catch {
    return false;
  }
}

async function deleteKey(key: string) {
  const client = await redis();
  if (!client) return false;
  try {
    await client.del(key);
    return true;
  } catch {
    return false;
  }
}

async function appendPendingChallenge(user: string, challengeId: string) {
  const existing = (await readJson<string[]>(pendingChallengesKey(user))) || [];
  const next = Array.from(new Set([...existing, challengeId]));
  await writeJson(pendingChallengesKey(user), next, challengeTtlSeconds);
}

async function markRetiredSession(user: string, sessionId: string) {
  if (!sessionId) return;
  await writeJson(retiredKey(user, sessionId), { retiredAt: now() }, retiredTtlSeconds);
  memoryRegistry().retiredSessions.set(retiredMemoryKey(user, sessionId), now());
}

async function isRetiredSession(user: string, sessionId: string) {
  if (!sessionId) return false;
  if (await readJson<{ retiredAt: number }>(retiredKey(user, sessionId))) return true;
  return memoryRegistry().retiredSessions.has(retiredMemoryKey(user, sessionId));
}

async function clearPendingChallenges(user: string, challengeId?: string) {
  const pending = new Set((await readJson<string[]>(pendingChallengesKey(user))) || []);
  if (challengeId) pending.add(challengeId);
  for (const id of pending) {
    await deleteKey(challengeKey(id));
  }
  await deleteKey(pendingChallengesKey(user));

  const store = memoryRegistry();
  for (const [id, challenge] of store.challenges.entries()) {
    if (challenge.user === user || pending.has(id)) store.challenges.delete(id);
  }
}

async function readActiveSession(user: string) {
  const active = await readJson<ActiveSession>(activeKey(user));
  if (active) return active;
  return memoryRegistry().activeSessions.get(user) || null;
}

export async function activateSession(user: string, sessionId: string) {
  if (await isRetiredSession(user, sessionId)) return;
  const session: ActiveSession = { user, sessionId, lastSeen: now() };
  if (await writeJson(activeKey(user), session, activeTtlSeconds)) return;
  memoryRegistry().activeSessions.set(user, session);
}

export async function retireSession(user: string, sessionId?: string) {
  const active = await readActiveSession(user);
  const retiredSessionId = sessionId || active?.sessionId || "";
  if (retiredSessionId) await markRetiredSession(user, retiredSessionId);
  await clearPendingChallenges(user, active?.challengeId);
  await deleteKey(activeKey(user));
  memoryRegistry().activeSessions.delete(user);
}

export async function getActiveSession(user: string) {
  const active = await readJson<ActiveSession>(activeKey(user));
  if (active && now() - active.lastSeen <= activeTtlMs && !(await isRetiredSession(user, active.sessionId))) return active;
  if (active) await deleteKey(activeKey(user));
  const memoryActive = memoryRegistry().activeSessions.get(user) || null;
  if (!memoryActive) return null;
  if (now() - memoryActive.lastSeen > activeTtlMs || (await isRetiredSession(user, memoryActive.sessionId))) {
    memoryRegistry().activeSessions.delete(user);
    return null;
  }
  return memoryActive;
}

export async function createLoginChallenge(context: BedoUserContext, requestedSessionId: string, challengeId: string) {
  const challenge: LoginChallenge = {
    challengeId,
    user: context.user,
    requestedSessionId,
    context: { ...context, session_id: requestedSessionId },
    createdAt: now(),
    status: "pending",
  };
  const active = await getActiveSession(context.user);
  if (await writeJson(challengeKey(challengeId), challenge, challengeTtlSeconds)) {
    await appendPendingChallenge(context.user, challengeId);
    if (active) await writeJson(activeKey(context.user), { ...active, challengeId }, activeTtlSeconds);
    return challenge;
  }
  const store = memoryRegistry();
  store.challenges.set(challengeId, challenge);
  if (active) store.activeSessions.set(context.user, { ...active, challengeId });
  return challenge;
}

export async function getLoginChallenge(challengeId: string) {
  const challenge = await readJson<LoginChallenge>(challengeKey(challengeId));
  if (challenge) return challenge;
  return memoryRegistry().challenges.get(challengeId) || null;
}

export async function consumeLoginChallenge(challengeId: string) {
  if (await deleteKey(challengeKey(challengeId))) return;
  memoryRegistry().challenges.delete(challengeId);
}

export async function retireUserSessions(user: string) {
  const active = await readActiveSession(user);
  if (active?.sessionId) await markRetiredSession(user, active.sessionId);
  await clearPendingChallenges(user, active?.challengeId);
  await deleteKey(activeKey(user));
  memoryRegistry().activeSessions.delete(user);
}

export async function allowLoginChallenge(challengeId: string, currentSession: BedoUserContext) {
  const challenge = await getLoginChallenge(challengeId);
  const active = await getActiveSession(currentSession.user);
  if (!challenge || challenge.user !== currentSession.user || !active || active.sessionId !== currentSession.session_id) return false;
  const nextChallenge = { ...challenge, status: "allowed" as const };
  await writeJson(challengeKey(challengeId), nextChallenge, challengeTtlSeconds);
  await activateSession(challenge.user, challenge.requestedSessionId);
  if (!(await redis())) {
    memoryRegistry().challenges.set(challengeId, nextChallenge);
  }
  return true;
}

export async function denyLoginChallenge(challengeId: string, currentSession: BedoUserContext) {
  const challenge = await getLoginChallenge(challengeId);
  const active = await getActiveSession(currentSession.user);
  if (!challenge || challenge.user !== currentSession.user || !active || active.sessionId !== currentSession.session_id) return false;
  const nextChallenge = { ...challenge, status: "denied" as const };
  const nextActive: ActiveSession = { ...active };
  delete nextActive.challengeId;
  await writeJson(challengeKey(challengeId), nextChallenge, challengeTtlSeconds);
  await writeJson(activeKey(currentSession.user), nextActive, activeTtlSeconds);
  if (!(await redis())) {
    const store = memoryRegistry();
    store.challenges.set(challengeId, nextChallenge);
    store.activeSessions.set(currentSession.user, nextActive);
  }
  return true;
}

export async function sessionStatus(session: BedoUserContext) {
  if (!session.session_id) return { valid: false as const, reason: "missing_session" };
  if (await isRetiredSession(session.user, session.session_id)) return { valid: false as const, reason: "retired_session" };
  const active = await getActiveSession(session.user);
  if (!active) {
    await activateSession(session.user, session.session_id);
    return { valid: true as const };
  }
  if (active.sessionId !== session.session_id) return { valid: false as const, reason: "replaced_session" };
  const refreshed = { ...active, lastSeen: now() };
  const challenge = refreshed.challengeId ? await getLoginChallenge(refreshed.challengeId) : null;
  if (refreshed.challengeId && !challenge) delete refreshed.challengeId;
  await writeJson(activeKey(session.user), refreshed, activeTtlSeconds);
  if (!(await redis())) memoryRegistry().activeSessions.set(session.user, refreshed);
  return {
    valid: true as const,
    conflict: challenge?.status === "pending" ? { challengeId: challenge.challengeId } : null,
  };
}

export function __resetSessionRegistryForTests() {
  globalThis.__bedoSessionRegistry = {
    activeSessions: new Map<string, ActiveSession>(),
    challenges: new Map<string, LoginChallenge>(),
    retiredSessions: new Map<string, number>(),
  };
  redisPromise = null;
}
