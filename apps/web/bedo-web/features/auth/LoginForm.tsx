"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

const loginErrorMessages: Record<string, string> = {
  already_signed_in: "This account is already signed in.",
  invalid: "Invalid username or password.",
  session_transferred: "Your session was transferred to another device.",
  session_replaced: "Your account was signed in on another device.",
  timeout: "Your session timed out because of inactivity.",
};

export function LoginForm({ initialError }: { initialError?: string }) {
  const [error, setError] = useState(initialError ? loginErrorMessages[initialError] || loginErrorMessages.invalid : "");
  const [waitingMessage, setWaitingMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  async function pollConflict(challengeId: string) {
    async function check() {
      const response = await fetch(`/api/auth/login-conflict?challengeId=${encodeURIComponent(challengeId)}`);
      if (response.status === 202) return;
      if (pollRef.current) window.clearInterval(pollRef.current);
      pollRef.current = null;
      setSubmitting(false);
      const data = await response.json().catch(() => ({}));
      if (response.ok && data.route) {
        window.location.assign(data.route);
        return;
      }
      setWaitingMessage("");
      setError(data.error || "This account is already signed in.");
    }
    await check();
    if (!pollRef.current) pollRef.current = window.setInterval(check, 2000);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setWaitingMessage("");
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password"),
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (response.ok && data.route) {
      window.location.assign(data.route);
      return;
    }
    if (response.status === 409 && data.challengeId) {
      setWaitingMessage("This account is already signed in. Waiting for the active session to allow or deny this login.");
      await pollConflict(String(data.challengeId));
      return;
    }
    setSubmitting(false);
    setError(data.error || "Invalid username or password.");
  }

  return (
    <form className="space-y-6" onSubmit={submit}>
      <label className="block">
        <span className="text-base font-semibold text-ink">Username</span>
        <input
          className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-4 py-4 text-base"
          name="username"
          autoComplete="username"
          required
        />
      </label>
      <label className="block">
        <span className="text-base font-semibold text-ink">Password</span>
        <input
          className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-4 py-4 text-base"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </label>
      {error && <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      {waitingMessage && <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-900">{waitingMessage}</div>}
      <button
        className="focus-ring inline-flex min-h-12 w-full items-center justify-center rounded-md bg-ink px-4 text-base font-semibold text-white transition hover:bg-steel disabled:cursor-not-allowed disabled:opacity-60"
        type="submit"
        disabled={submitting}
      >
        {submitting ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
