/** @type {import('next').NextConfig} */
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig = {
  // Native @next/swc-win32-x64-msvc is often blocked by Windows Application Control.
  // Use .mjs (not .ts) so Next does not need native SWC just to read this file.
  experimental: {
    useWasmBinary: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
