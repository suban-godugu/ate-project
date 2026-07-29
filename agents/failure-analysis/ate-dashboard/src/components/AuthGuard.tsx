"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { appConfig } from "@/lib/config";
import { canAccessRoute } from "@/lib/rbac";
import { useAuthStore } from "@/stores/authStore";
import { logger } from "@/lib/logger";

/** Sets session cookie for proxy auth gate and redirects unauthorized users. */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const hydrated = useAuthStore((s) => s.hydrated);

  useEffect(() => {
    logger.route(pathname);
  }, [pathname]);

  useEffect(() => {
    if (!appConfig.authEnabled) return;
    if (!hydrated) return;

    const isLogin = pathname.startsWith("/login");

    if (accessToken) {
      document.cookie = `fa_session=1; path=/; SameSite=Lax; max-age=${60 * 60 * 24 * 7}`;
    } else {
      document.cookie = "fa_session=; path=/; Max-Age=0";
    }

    if (!accessToken && !isLogin) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }

    if (accessToken && isLogin) {
      router.replace("/overview");
      return;
    }

    if (user && !isLogin && !canAccessRoute(user.role, pathname)) {
      router.replace("/overview");
    }
  }, [accessToken, hydrated, pathname, router, user]);

  if (appConfig.authEnabled && !hydrated && !pathname.startsWith("/login")) {
    return (
      <div className="p-8 text-sm text-[var(--muted)]" role="status">
        Restoring session…
      </div>
    );
  }

  return <>{children}</>;
}
