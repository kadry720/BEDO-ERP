"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/Button";

export function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setPending(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password")
      })
    });
    const data = await response.json();
    setPending(false);
    if (!response.ok) {
      setError(data.error || "Invalid username or password.");
      return;
    }
    router.replace(data.route || "/access-not-configured");
    router.refresh();
  }

  return (
    <form className="space-y-5" onSubmit={onSubmit}>
      <label className="block">
        <span className="text-sm font-semibold text-ink">Username</span>
        <input
          className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-3 text-sm"
          name="username"
          autoComplete="username"
          required
        />
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-ink">Password</span>
        <input
          className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-3 text-sm"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </label>
      {error && <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      <Button className="w-full" disabled={pending} type="submit">
        {pending ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}
