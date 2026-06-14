import Redis from "ioredis";
import type { BedoUserContext } from "@/lib/routes";
import { isLocalMode, optionalRedisUrl } from "@/server/config";

const activeTtlMs = 8 * 60 * 60 * 1000;
const challengeTtlMs = 2 * 60 * 1000;
const activeTtlSeconds = Math.floor(activeTtlMs / 1000);
const challengeTtlSeconds = Math.floor(challengeTtlMs / 1000);

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
}

function activeKey(user: string) {
  return `bedo:session:active:${user}`;
}

function challengeKey(challengeId: string) {
  return `bedo:session:challenge:${challengeId}`;
}

async function redis() {
  const url = optionalRedisUrl();
  if (!url || process.env.BEDO_DISABLE_SESSION_REDIS === "1") return null;
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

export async function activateSession(user: string, sessionId: string) {
  const session: ActiveSession = { user, sessionId, lastSeen: now() };
  if (await writeJson(activeKey(user), session, activeTtlSeconds)) return;
  memoryRegistry().activeSessions.set(user, session);
}

export async function retireSession(user: string, sessionId?: string) {
  const active = await getActiveSession(user);
  if (!active) return;
  if (sessionId && active.sessionId !== sessionId) return;
  if (await deleteKey(activeKey(user))) return;
  memoryRegistry().activeSessions.delete(user);
}

export async function getActiveSession(user: string) {
  const active = await readJson<ActiveSession>(activeKey(user));
  if (active && now() - active.lastSeen <= activeTtlMs) return active;
  if (active) await deleteKey(activeKey(user));
  return memoryRegistry().activeSessions.get(user) || null;
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
  };
  redisPromise = null;
}
