/** Same-origin embed paths — public UI is only http://localhost:3000/dashboard. */

export const AGENT_EMBED_PATHS = {
  pattern: "/embed/pattern",
  failure: "/embed/failure/overview",
  scan: "/embed/scan",
  patternRec: "/embed/pattern-rec/",
  scanDebugRec: "/embed/scan-debug-rec/dashboard/recommendation-analysis",
  testOpt: "/embed/test-opt/",
} as const;

export type AgentEmbedKey = keyof typeof AGENT_EMBED_PATHS;

/**
 * Vite agents mount `<BrowserRouter basename={import.meta.env.BASE_URL}>`, and
 * React Router only matches when the pathname starts with that basename —
 * including its trailing slash. Without it the router renders an empty tree.
 */
const ROUTER_BASENAME_ROOTS = ["/embed/pattern-rec", "/embed/test-opt"];

function ensureRouterBasename(path: string): string {
  const [pathname, search] = path.split("?");
  if (!ROUTER_BASENAME_ROOTS.includes(pathname)) return path;
  return search ? `${pathname}/?${search}` : `${pathname}/`;
}

/** Prefer health.embed_path when present; otherwise the fixed same-origin path. */
export function resolveAgentEmbedUrl(
  embedPathFromHealth: string | null | undefined,
  fallbackKey: AgentEmbedKey
): string {
  const fromHealth = embedPathFromHealth?.trim();
  if (fromHealth) {
    if (fromHealth.startsWith("/")) return ensureRouterBasename(fromHealth);
    try {
      const u = new URL(fromHealth);
      return ensureRouterBasename(`${u.pathname}${u.search}` || AGENT_EMBED_PATHS[fallbackKey]);
    } catch {
      return AGENT_EMBED_PATHS[fallbackKey];
    }
  }
  return AGENT_EMBED_PATHS[fallbackKey];
}
