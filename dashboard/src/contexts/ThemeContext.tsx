"use client";

import { useEffect } from "react";
import {
  applyThemeToDocument,
  accentMap,
  useThemeStore,
} from "@/stores/themeStore";
import { useThemePreferencesSync } from "@/hooks/useThemePreferencesSync";
import { defaultThemeConfig, type ThemeConfig } from "@/types/theme";

interface ThemeContextValue {
  theme: ThemeConfig;
  updateTheme: (partial: Partial<ThemeConfig>) => void;
  resetTheme: () => void;
  accentHex: string;
}

export { accentMap };

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useThemeStore((s) => s.theme);
  useThemePreferencesSync();

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  return <>{children}</>;
}

export function useTheme(): ThemeContextValue {
  const theme = useThemeStore((s) => s.theme);
  const updateTheme = useThemeStore((s) => s.updateTheme);
  const resetTheme = useThemeStore((s) => s.resetTheme);
  return {
    theme,
    updateTheme,
    resetTheme,
    accentHex: accentMap[theme.primaryColor],
  };
}
