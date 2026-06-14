/** @type {import('next').NextConfig} */
const nextConfig = {
  poweredByHeader: false,
  typedRoutes: false,
  devIndicators: false,
  allowedDevOrigins: ["172.20.88.65", "192.168.1.101", "127.0.0.1", "localhost"]
};

export default nextConfig;
