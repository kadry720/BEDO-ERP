const placeholderSecretFragments = [
  "replace-me",
  "change-this",
  "local-dev-password",
  "local-seed-password",
];

export function isLocalMode() {
  const mode = (process.env.BEDO_ENV || process.env.NODE_ENV || "development").toLowerCase();
  return ["local", "dev", "development", "test"].includes(mode);
}

export function requireConfiguredSecret(name: string) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is not configured.`);
  const lowered = value.toLowerCase();
  if (!isLocalMode() && placeholderSecretFragments.some((fragment) => lowered.includes(fragment))) {
    throw new Error(`${name} is using a placeholder value outside local development.`);
  }
  return value;
}

export function optionalRedisUrl() {
  return process.env.BEDO_SESSION_REDIS_URL || process.env.REDIS_CACHE_URL || "";
}
