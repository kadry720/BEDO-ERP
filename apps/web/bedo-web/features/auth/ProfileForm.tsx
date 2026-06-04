"use client";

import { useState } from "react";
import { Button } from "@/components/Button";

type Profile = {
  user: string;
  username: string;
  first_name: string;
  middle_name: string;
  last_name: string;
};

export function ProfileForm({ profile }: { profile: Profile }) {
  const [message, setMessage] = useState("");

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    const form = new FormData(event.currentTarget);
    const response = await fetch("/api/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        first_name: form.get("first_name"),
        middle_name: form.get("middle_name"),
        last_name: form.get("last_name")
      })
    });
    setMessage(response.ok ? "Profile updated." : "Profile update failed.");
  }

  return (
    <form className="max-w-3xl space-y-5 rounded-md border border-gray-200 bg-white p-6 shadow-panel" onSubmit={onSubmit}>
      <div>
        <div className="text-xs font-semibold uppercase text-muted">My Profile</div>
        <h1 className="mt-2 text-3xl font-bold text-ink">Profile details</h1>
        <p className="mt-3 text-sm text-muted">Only your basic identity fields are editable in BEDO.</p>
      </div>
      {[
        ["username", "Username"],
        ["first_name", "First name"],
        ["middle_name", "Middle name"],
        ["last_name", "Last name"]
      ].map(([name, label]) => (
        <label key={name} className="block">
          <span className="text-sm font-semibold text-ink">{label}</span>
          <input
            className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            name={name}
            defaultValue={profile[name as keyof Profile]}
            required={name !== "middle_name" && name !== "last_name"}
          />
        </label>
      ))}
      {message && <div className="text-sm font-semibold text-muted">{message}</div>}
      <Button type="submit">Save profile</Button>
    </form>
  );
}
