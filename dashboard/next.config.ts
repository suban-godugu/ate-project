import type { NextConfig } from "next";

/** Internal agent UI ports — proxied under /embed/* so the browser only uses :3000. */
const EMBED_TARGETS = {
  pattern: process.env.EMBED_PATTERN_URL ?? "http://127.0.0.1:8011",
  failure: process.env.EMBED_FAILURE_URL ?? "http://127.0.0.1:3020",
  scan: process.env.EMBED_SCAN_URL ?? "http://127.0.0.1:3030",
  patternRec: process.env.EMBED_PATTERN_REC_URL ?? "http://127.0.0.1:3041",
  patternRecApi:
    process.env.EMBED_PATTERN_REC_API_URL ?? "http://127.0.0.1:8041",
  scanDebugRec: process.env.EMBED_SCAN_DEBUG_REC_URL ?? "http://127.0.0.1:3042",
  testOpt: process.env.EMBED_TEST_OPT_URL ?? "http://127.0.0.1:3043",
  testOptApi: process.env.EMBED_TEST_OPT_API_URL ?? "http://127.0.0.1:8043",
} as const;

const nextConfig: NextConfig = {
  // Hide Next.js floating "N" badge in the enterprise UI
  devIndicators: false,
  // Vite agents mount React Router with basename "<embed base>/", so the embed
  // URL must keep its trailing slash instead of being 308'd to the bare path.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      {
        source: "/embed/pattern",
        destination: EMBED_TARGETS.pattern,
      },
      {
        source: "/embed/pattern/:path*",
        destination: `${EMBED_TARGETS.pattern}/:path*`,
      },
      {
        source: "/embed/failure",
        destination: `${EMBED_TARGETS.failure}/embed/failure`,
      },
      {
        source: "/embed/failure/:path*",
        destination: `${EMBED_TARGETS.failure}/embed/failure/:path*`,
      },
      {
        source: "/embed/scan",
        destination: `${EMBED_TARGETS.scan}/embed/scan`,
      },
      {
        source: "/embed/scan/:path*",
        destination: `${EMBED_TARGETS.scan}/embed/scan/:path*`,
      },
      {
        source: "/embed/pattern-rec/api-proxy/:path*",
        destination: `${EMBED_TARGETS.patternRecApi}/:path*`,
      },
      {
        source: "/embed/pattern-rec",
        destination: `${EMBED_TARGETS.patternRec}/embed/pattern-rec/`,
      },
      {
        source: "/embed/pattern-rec/",
        destination: `${EMBED_TARGETS.patternRec}/embed/pattern-rec/`,
      },
      {
        source: "/embed/pattern-rec/:path*",
        destination: `${EMBED_TARGETS.patternRec}/embed/pattern-rec/:path*`,
      },
      {
        source: "/embed/scan-debug-rec",
        destination: `${EMBED_TARGETS.scanDebugRec}/embed/scan-debug-rec`,
      },
      {
        source: "/embed/scan-debug-rec/:path*",
        destination: `${EMBED_TARGETS.scanDebugRec}/embed/scan-debug-rec/:path*`,
      },
      {
        source: "/embed/test-opt/api-proxy/:path*",
        destination: `${EMBED_TARGETS.testOptApi}/:path*`,
      },
      {
        source: "/embed/test-opt",
        destination: `${EMBED_TARGETS.testOpt}/embed/test-opt/`,
      },
      {
        source: "/embed/test-opt/",
        destination: `${EMBED_TARGETS.testOpt}/embed/test-opt/`,
      },
      {
        source: "/embed/test-opt/:path*",
        destination: `${EMBED_TARGETS.testOpt}/embed/test-opt/:path*`,
      },
    ];
  },
};

export default nextConfig;
