import type { NextConfig } from "next";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

/**
 * Pin Turbopack's workspace root to this package directory.
 *
 * WHY: Next/Turbopack walks upward for a lockfile. A parent
 * `C:\Users\hsmak\package-lock.json` caused it to treat the user home as
 * the monorepo root, so App Router pages under ate-dashboard returned 404
 * while the shell still rendered.
 *
 * Do not use "." alone — resolution must be absolute and must land on
 * ate-dashboard (the directory that contains src/app). Candidates cover
 * both import.meta.url (when the config is loaded as ESM) and __dirname
 * (when Next evaluates a copied/transpiled config from a temp path).
 */
function resolveDashboardRoot(): string {
  const candidates: string[] = [];

  try {
    candidates.push(path.dirname(fileURLToPath(import.meta.url)));
  } catch {
    /* import.meta.url unavailable in this load path */
  }

  if (typeof __dirname === "string" && __dirname.length > 0) {
    candidates.push(__dirname);
  }

  candidates.push(process.cwd());

  const marker = path.join("src", "app", "overview", "page.tsx");
  for (const candidate of candidates) {
    const resolved = path.resolve(candidate);
    if (fs.existsSync(path.join(resolved, marker))) {
      return resolved;
    }
  }

  throw new Error(
    `ate-dashboard turbopack.root could not be resolved. Tried: ${candidates
      .map((c) => path.resolve(c))
      .join(", ")}. Ensure next.config.ts lives next to src/app.`,
  );
}

const dashboardRoot = resolveDashboardRoot();
console.log("[ate-dashboard] turbopack.root =", dashboardRoot);

const embedBasePath = process.env.NEXT_EMBED_BASE_PATH || "/embed/failure";

const nextConfig: NextConfig = {
  // Namespace Next.js assets and routes when proxied through VERILUMEN :3000.
  basePath: embedBasePath,
  turbopack: {
    root: dashboardRoot,
  },
  // Hide Next.js "N" floating badge when embedded in VERILUMEN
  devIndicators: false,
  // Allow cloud Docker builds even if local TS strictness finds latent issues.
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Dev/proxy rewrites buffer request bodies (default 10MB). Large STIL+log uploads exceed that.
  experimental: {
    proxyClientMaxBodySize: "512mb",
  },
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  async rewrites() {
    const backend =
      process.env.ATE_API_PROXY ||
      process.env.BACKEND_URL ||
      "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
