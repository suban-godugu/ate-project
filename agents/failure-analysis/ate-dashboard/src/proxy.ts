import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js 16 proxy (replaces deprecated middleware convention):
 * redirect unauthenticated users to /login when auth is enabled.
 * Auth cookie is mirrored from the client session; when AUTH is disabled
 * via env, all routes pass through.
 */
const PUBLIC = ["/login"];

export function proxy(request: NextRequest) {
  const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";
  if (!authEnabled) return NextResponse.next();

  const { pathname } = request.nextUrl;
  if (
    PUBLIC.some((p) => pathname.startsWith(p)) ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Soft gate: cookie set by AuthGuard after login. Client also enforces redirect.
  const session = request.cookies.get("fa_session")?.value;
  if (!session) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
