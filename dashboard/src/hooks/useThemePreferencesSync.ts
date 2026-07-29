"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api/auth";
import { isLiveApi } from "@/lib/api/config";
import { useThemeStore } from "@/stores/themeStore";
import { useUserStore } from "@/stores/userStore";
import { defaultThemeConfig, type ThemeConfig } from "@/types/theme";

const SYNC_DEBOUNCE_MS = 500;

function mergeTheme(remote: Record<string, unknown>): Partial<ThemeConfig> {
  const merged: Partial<ThemeConfig> = {};
  for (const key of Object.keys(defaultThemeConfig) as (keyof ThemeConfig)[]) {
    const value = remote[key];
    if (value !== undefined && value !== null) {
      (merged as Record<string, unknown>)[key] = value;
    }
  }
  return merged;
}

export function useThemePreferencesSync() {
  const theme = useThemeStore((s) => s.theme);
  const updateTheme = useThemeStore((s) => s.updateTheme);
  const isAuthenticated = useUserStore((s) => s.isAuthenticated);
  const queryClient = useQueryClient();
  const hydratedRef = useRef(false);
  const skipPushRef = useRef(false);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!isLiveApi() || !isAuthenticated) {
      hydratedRef.current = false;
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        const prefs = await authApi.getPreferences();
        if (cancelled) return;
        if (prefs.theme_json && typeof prefs.theme_json === "object") {
          skipPushRef.current = true;
          updateTheme(mergeTheme(prefs.theme_json));
        }
        hydratedRef.current = true;
        await queryClient.invalidateQueries({ queryKey: ["preferences"] });
      } catch {
        if (!cancelled) hydratedRef.current = true;
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, updateTheme, queryClient]);

  useEffect(() => {
    if (!isLiveApi() || !isAuthenticated || !hydratedRef.current) return;
    if (skipPushRef.current) {
      skipPushRef.current = false;
      return;
    }

    const timer = setTimeout(async () => {
      try {
        await authApi.updatePreferences({
          theme_json: theme as unknown as Record<string, unknown>,
        });
        await queryClient.invalidateQueries({ queryKey: ["preferences"] });
        await queryClient.invalidateQueries({ queryKey: ["user"] });
      } catch {
        if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
        retryTimerRef.current = setTimeout(async () => {
          try {
            await authApi.updatePreferences({
              theme_json: theme as unknown as Record<string, unknown>,
            });
            await queryClient.invalidateQueries({ queryKey: ["preferences"] });
          } catch {
            /* keep local theme until next change */
          }
        }, 5000);
      }
    }, SYNC_DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [theme, isAuthenticated, queryClient]);
}
