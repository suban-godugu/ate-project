"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import { clearSessionTokens, refreshAccessToken } from "@/lib/api/authRefresh";
import { getAccessToken, isLiveApi } from "@/lib/api/config";
import { useUserStore } from "@/stores/userStore";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useUserStore((s) => s.isAuthenticated);
  const setSession = useUserStore((s) => s.setSession);
  const clearSession = useUserStore((s) => s.clearSession);
  const [restoring, setRestoring] = useState(isLiveApi());

  useEffect(() => {
    if (!isLiveApi()) {
      setRestoring(false);
      return;
    }

    let cancelled = false;

    async function restore() {
      // Always revalidate against the API in live mode. Persisted Zustand
      // isAuthenticated can outlive expired JWTs / Redis session keys.
      const token = getAccessToken();
      if (!token) {
        if (!cancelled) {
          clearSession();
          clearSessionTokens();
          setRestoring(false);
          router.replace("/login");
        }
        return;
      }

      try {
        const user = await authApi.getMe();
        if (!cancelled) setSession(user, getAccessToken() ?? token);
      } catch {
        let refreshed: string | null = null;
        try {
          refreshed = await refreshAccessToken();
        } catch {
          refreshed = null;
        }
        if (refreshed) {
          try {
            const user = await authApi.getMe();
            if (!cancelled) {
              setSession(user, refreshed);
              return;
            }
          } catch {
            /* fall through */
          }
        }
        if (!cancelled) {
          clearSession();
          clearSessionTokens();
          router.replace("/login");
        }
      } finally {
        if (!cancelled) setRestoring(false);
      }
    }

    restore();
    return () => {
      cancelled = true;
    };
    // Run once on mount for live API session restore.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isLiveApi() && !restoring && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, restoring, router]);

  if (isLiveApi() && (restoring || !isAuthenticated)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#090B12] text-slate-400">
        {restoring ? "Restoring session…" : "Redirecting to login…"}
      </div>
    );
  }

  return <>{children}</>;
}
