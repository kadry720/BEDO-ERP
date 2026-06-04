"use client";

import { useState } from "react";
import { Button } from "@/components/Button";

type Profile = {
  user: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
};

const fields = [
  ["username", "Username", "text"],
  ["password", "New password", "password"],
  ["first_name", "First name", "text"],
  ["last_name", "Last name", "text"],
  ["email", "Email", "email"],
  ["phone_number", "Phone", "tel"]
];

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
        password: form.get("password"),
        first_name: form.get("first_name"),
        last_name: form.get("last_name"),
        email: form.get("email"),
        phone_number: form.get("phone_number")
      })
    });
    setMessage(response.ok ? "Profile updated." : "Profile update failed.");
  }

  return (
    <form className="max-w-5xl space-y-6 rounded-md border border-gray-200 bg-white p-6 shadow-panel" onSubmit={onSubmit}>
      <div>
        <div className="text-xs font-semibold uppercase text-muted">My Profile</div>
        <h1 className="mt-2 text-3xl font-bold text-ink">Profile details</h1>
        <p className="mt-3 text-sm text-muted">Update your BEDO account identity and contact details.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {fields.map(([name, label, type]) => (
          <label key={name} className="block">
            <span className="text-sm font-semibold text-ink">{label}</span>
            <input
              className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              name={name}
              type={type}
              defaultValue={name === "password" ? "" : String(profile[name as keyof Profile] || "")}
              required={name !== "password"}
              autoComplete={name === "password" ? "new-password" : undefined}
            />
          </label>
        ))}
      </div>
      {message && <div className="text-sm font-semibold text-muted">{message}</div>}
      <Button type="submit">Save profile</Button>
    </form>
  );
}
