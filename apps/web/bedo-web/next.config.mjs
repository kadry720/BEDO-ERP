function hostFromOrigin(value) {
  if (!value) return "";
  try {
    return new URL(value).host;
  } catch {
    return String(value).replace(/^https?:\/\//, "").replace(/\/$/, "");
  }
}

function allowedDevOrigins() {
  const configured = (process.env.BEDO_WEB_ALLOWED_DEV_ORIGINS || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .map(hostFromOrigin);
  const publicHost = hostFromOrigin(process.env.BEDO_WEB_PUBLIC_URL || "");
  return Array.from(new Set(["localhost", "127.0.0.1", publicHost, ...configured].filter(Boolean)));
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  poweredByHeader: false,
  typedRoutes: false,
  devIndicators: false,
  allowedDevOrigins: allowedDevOrigins()
};

export default nextConfig;
