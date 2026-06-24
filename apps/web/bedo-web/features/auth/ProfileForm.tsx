"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, CheckCircle2, Eye, EyeOff, KeyRound, Loader2, Save, ShieldCheck, UserRound } from "lucide-react";
import { Button } from "@/components/Button";
import type { BedoUserContext } from "@/lib/routes";

export type Profile = {
  user: string;
  username: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  email: string;
  phone_number: string;
};

type FieldErrors = Partial<Record<keyof Profile | "current_password" | "new_password" | "confirm_password", string>>;

type PasswordState = {
  current_password: string;
  new_password: string;
  confirm_password: string;
};

const emptyPasswordState: PasswordState = {
  current_password: "",
  new_password: "",
  confirm_password: "",
};

function displayName(profile: Profile) {
  return [profile.first_name, profile.middle_name, profile.last_name].filter(Boolean).join(" ") || profile.username;
}

function initialsFor(profile: Profile) {
  const source = [profile.first_name, profile.last_name].filter(Boolean);
  if (!source.length) return profile.username.slice(0, 2).toUpperCase();
  return source.map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}

export function ProfileForm({ profile, session }: { profile: Profile; session: BedoUserContext }) {
  const router = useRouter();
  const [formState, setFormState] = useState<Profile>({ ...profile, middle_name: profile.middle_name || "" });
  const [passwordState, setPasswordState] = useState<PasswordState>(emptyPasswordState);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [backendError, setBackendError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const initials = useMemo(() => initialsFor(formState), [formState]);
  const originalProfile = useMemo(() => ({ ...profile, middle_name: profile.middle_name || "" }), [profile]);
  const profileDirty = useMemo(
    () => (["username", "first_name", "middle_name", "last_name", "email", "phone_number"] as const).some((field) => formState[field] !== originalProfile[field]),
    [formState, originalProfile]
  );
  const passwordDirty = Object.values(passwordState).some(Boolean);

  function updateProfileField(field: keyof Profile, value: string) {
    setFormState((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => ({ ...current, [field]: "" }));
  }

  function updatePasswordField(field: keyof PasswordState, value: string) {
    setPasswordState((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => ({ ...current, [field]: "" }));
  }

  function validate() {
    const nextErrors: FieldErrors = {};
    if (!formState.username.trim()) nextErrors.username = "Username is required.";
    if (!formState.first_name.trim()) nextErrors.first_name = "First name is required.";
    if (!formState.last_name.trim()) nextErrors.last_name = "Last name is required.";
    if (!formState.email.trim()) nextErrors.email = "Email is required.";
    if (!formState.phone_number.trim()) nextErrors.phone_number = "Phone is required.";

    const wantsPasswordChange = Boolean(passwordState.current_password || passwordState.new_password || passwordState.confirm_password);
    if (wantsPasswordChange) {
      if (!passwordState.current_password) nextErrors.current_password = "Current password is required.";
      if (!passwordState.new_password) nextErrors.new_password = "New password is required.";
      if (passwordState.new_password !== passwordState.confirm_password) {
        nextErrors.confirm_password = "Password confirmation must match.";
      }
    }

    setFieldErrors(nextErrors);
    return Object.values(nextErrors).every((value) => !value);
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBackendError("");
    setSuccess("");
    if (!validate()) return;

    setSaving(true);
    const response = await fetch("/api/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...formState,
        ...passwordState,
      }),
    });
    const data = await response.json().catch(() => ({}));
    setSaving(false);

    if (!response.ok) {
      setBackendError(data.error || "Profile could not be updated.");
      return;
    }

    if (data.profile) {
      setFormState({ ...data.profile, middle_name: data.profile.middle_name || "" });
    }
    setPasswordState(emptyPasswordState);
    setSuccess(data.password_changed ? "Profile and password updated." : "Profile updated.");
    router.refresh();
  }

  return (
    <form className="space-y-6" onSubmit={onSubmit}>
      <section className="grid gap-5 lg:grid-cols-[360px_1fr]">
        <aside className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-md bg-ink text-xl font-black text-white">
              {initials}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-xs font-bold uppercase text-muted">
                <UserRound className="h-4 w-4" />
                Account
              </div>
              <h1 className="mt-2 truncate text-2xl font-black text-ink">{displayName(formState)}</h1>
              <p className="mt-1 truncate text-sm font-semibold text-muted">{formState.username}</p>
            </div>
          </div>
          <div className="mt-5 border-t border-gray-100 pt-4">
            <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase text-muted">
              <ShieldCheck className="h-4 w-4" />
              Roles
            </div>
            <div className="flex flex-wrap gap-2">
              {session.roles.map((role) => (
                <span key={role} className="rounded bg-gray-100 px-2 py-1 text-xs font-bold text-gray-700">
                  {role}
                </span>
              ))}
            </div>
          </div>
          {(profileDirty || passwordDirty) && (
            <div className="mt-5 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-black uppercase tracking-wide text-amber-800">
              Unsaved changes
            </div>
          )}
        </aside>

        <div className="space-y-5">
          {success && (
            <div className="flex items-center gap-2 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm font-semibold text-green-800">
              <CheckCircle2 className="h-4 w-4" />
              {success}
            </div>
          )}
          {backendError && (
            <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">
              <AlertCircle className="h-4 w-4" />
              {backendError}
            </div>
          )}

          <section className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
            <div>
              <div className="text-xs font-bold uppercase text-muted">Personal Details</div>
              <h2 className="mt-1 text-xl font-black text-ink">Identity and contact</h2>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <TextField label="Username" name="username" value={formState.username} error={fieldErrors.username} onChange={updateProfileField} />
              <TextField label="Email" name="email" type="email" value={formState.email} error={fieldErrors.email} onChange={updateProfileField} />
              <TextField label="First name" name="first_name" value={formState.first_name} error={fieldErrors.first_name} onChange={updateProfileField} />
              <TextField label="Middle name" name="middle_name" value={formState.middle_name || ""} error={fieldErrors.middle_name} onChange={updateProfileField} />
              <TextField label="Last name" name="last_name" value={formState.last_name} error={fieldErrors.last_name} onChange={updateProfileField} />
              <TextField label="Phone" name="phone_number" type="tel" value={formState.phone_number} error={fieldErrors.phone_number} onChange={updateProfileField} />
            </div>
          </section>

          <section className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
            <div className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-ember" />
              <div>
                <div className="text-xs font-bold uppercase text-muted">Security</div>
                <h2 className="text-xl font-black text-ink">Password</h2>
              </div>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <PasswordField
                label="Current password"
                name="current_password"
                value={passwordState.current_password}
                error={fieldErrors.current_password}
                autoComplete="current-password"
                onChange={updatePasswordField}
              />
              <PasswordField
                label="New password"
                name="new_password"
                value={passwordState.new_password}
                error={fieldErrors.new_password}
                autoComplete="new-password"
                onChange={updatePasswordField}
              />
              <PasswordField
                label="Confirm password"
                name="confirm_password"
                value={passwordState.confirm_password}
                error={fieldErrors.confirm_password}
                autoComplete="new-password"
                onChange={updatePasswordField}
              />
            </div>
          </section>

          <div className="flex justify-end">
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {saving ? "Saving..." : "Save account"}
            </Button>
          </div>
        </div>
      </section>
    </form>
  );
}

function TextField({
  label,
  name,
  type = "text",
  value,
  error,
  onChange,
}: {
  label: string;
  name: keyof Profile;
  type?: string;
  value: string;
  error?: string;
  onChange: (field: keyof Profile, value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-ink">{label}</span>
      <input
        className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        name={name}
        type={type}
        value={value}
        onChange={(event) => onChange(name, event.target.value)}
      />
      {error && <span className="mt-1 block text-xs font-semibold text-red-700">{error}</span>}
    </label>
  );
}

function PasswordField({
  label,
  name,
  value,
  error,
  autoComplete,
  onChange,
}: {
  label: string;
  name: keyof PasswordState;
  value: string;
  error?: string;
  autoComplete: string;
  onChange: (field: keyof PasswordState, value: string) => void;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <label className="block">
      <span className="text-sm font-bold text-ink">{label}</span>
      <span className="mt-2 flex rounded-md border border-gray-300 bg-white focus-within:ring-2 focus-within:ring-amber-400">
        <input
          className="w-full rounded-l-md border-0 px-3 py-2 text-sm outline-none"
          name={name}
          type={visible ? "text" : "password"}
          value={value}
          autoComplete={autoComplete}
          onChange={(event) => onChange(name, event.target.value)}
        />
        <button
          className="inline-flex w-10 shrink-0 items-center justify-center rounded-r-md text-slate-500 hover:bg-slate-50 hover:text-slate-900"
          type="button"
          onClick={() => setVisible((current) => !current)}
          aria-label={visible ? `Hide ${label}` : `Show ${label}`}
        >
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </span>
      {error && <span className="mt-1 block text-xs font-semibold text-red-700">{error}</span>}
    </label>
  );
}
