import type { NextConfig } from "next";

/**
 * API proxy is handled by `src/app/scan-debug-api/[...path]/route.ts`
 * so the server can attach API_KEY without exposing it to the browser.
 */
const nextConfig: NextConfig = {
  // Namespace Next.js assets and routes when proxied through VERILUMEN :3000.
  basePath: process.env.NEXT_EMBED_BASE_PATH || "/embed/scan-debug-rec",
  reactStrictMode: false,
};

export default nextConfig;
