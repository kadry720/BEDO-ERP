import type { BedoUserContext } from "@/lib/routes";

const activeTtlMs = 8 * 60 * 60 * 1000;
const challengeTtlMs = 2 * 60 * 1000;

type ActiveSession = {
  user: string;
  sessionId: string;
  lastSeen: number;
  challengeId?: string;
};

type LoginChallenge = {
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

function registry() {
  if (!globalThis.__bedoSessionRegistry) {
    globalThis.__bedoSessionRegistry = {
      activeSessions: new Map<string, ActiveSession>(),
      challenges: new Map<string, LoginChallenge>(),
    };
  }
  cleanupExpired();
  return globalThis.__bedoSessionRegistry;
}

function now() {
  return Date.now();
}

function cleanupExpired() {
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

export function activateSession(user: string, sessionId: string) {
  registry().activeSessions.set(user, { user, sessionId, lastSeen: now() });
}

export function retireSession(user: string, sessionId?: string) {
  const store = registry();
  const active = store.activeSessions.get(user);
  if (!active) return;
  if (!sessionId || active.sessionId === sessionId) store.activeSessions.delete(user);
}

export function getActiveSession(user: string) {
  return registry().activeSessions.get(user) || null;
}

export function createLoginChallenge(context: BedoUserContext, requestedSessionId: string, challengeId: string) {
  const store = registry();
  const challenge: LoginChallenge = {
    challengeId,
    user: context.user,
    requestedSessionId,
    context: { ...context, session_id: requestedSessionId },
    createdAt: now(),
    status: "pending",
  };
  store.challenges.set(challengeId, challenge);
  const active = store.activeSessions.get(context.user);
  if (active) store.activeSessions.set(context.user, { ...active, challengeId });
  return challenge;
}

export function getLoginChallenge(challengeId: string) {
  return registry().challenges.get(challengeId) || null;
}

export function consumeLoginChallenge(challengeId: string) {
  registry().challenges.delete(challengeId);
}

export function allowLoginChallenge(challengeId: string, currentSession: BedoUserContext) {
  const store = registry();
  const challenge = store.challenges.get(challengeId);
  const active = store.activeSessions.get(currentSession.user);
  if (!challenge || challenge.user !== currentSession.user || !active || active.sessionId !== currentSession.session_id) return false;
  challenge.status = "allowed";
  store.challenges.set(challengeId, challenge);
  store.activeSessions.set(challenge.user, {
    user: challenge.user,
    sessionId: challenge.requestedSessionId,
    lastSeen: now(),
  });
  return true;
}

export function denyLoginChallenge(challengeId: string, currentSession: BedoUserContext) {
  const store = registry();
  const challenge = store.challenges.get(challengeId);
  const active = store.activeSessions.get(currentSession.user);
  if (!challenge || challenge.user !== currentSession.user || !active || active.sessionId !== currentSession.session_id) return false;
  challenge.status = "denied";
  store.challenges.set(challengeId, challenge);
  const nextActive: ActiveSession = { ...active };
  delete nextActive.challengeId;
  store.activeSessions.set(currentSession.user, nextActive);
  return true;
}

export function sessionStatus(session: BedoUserContext) {
  if (!session.session_id) return { valid: false as const, reason: "missing_session" };
  const store = registry();
  const active = store.activeSessions.get(session.user);
  if (!active) {
    activateSession(session.user, session.session_id);
    return { valid: true as const };
  }
  if (active.sessionId !== session.session_id) return { valid: false as const, reason: "replaced_session" };
  active.lastSeen = now();
  store.activeSessions.set(session.user, active);
  const challenge = active.challengeId ? store.challenges.get(active.challengeId) : null;
  return {
    valid: true as const,
    conflict: challenge?.status === "pending" ? { challengeId: challenge.challengeId } : null,
  };
}
