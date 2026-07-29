import { create } from "zustand";
import { persist } from "zustand/middleware";
import { defaultThemeConfig, type ThemeConfig } from "@/types/theme";

interface ThemeStore {
  theme: ThemeConfig;
  updateTheme: (partial: Partial<ThemeConfig>) => void;
  resetTheme: () => void;
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: defaultThemeConfig,
      updateTheme: (partial) =>
        set((state) => ({ theme: { ...state.theme, ...partial } })),
      resetTheme: () => set({ theme: defaultThemeConfig }),
    }),
    { name: "ate-theme-config" }
  )
);

export const accentMap = {
  purple: "#7C3AED",
  blue: "#2563EB",
  emerald: "#059669",
  orange: "#EA580C",
  red: "#DC2626",
} as const;

const fontSizeMap = {
  small: "14px",
  medium: "16px",
  large: "18px",
} as const;

const radiusMap = {
  small: "12px",
  medium: "20px",
  large: "24px",
} as const;

const sidebarWidthMap = {
  compact: "240px",
  standard: "280px",
  expanded: "320px",
} as const;

export function applyThemeToDocument(theme: ThemeConfig) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  const accent = accentMap[theme.primaryColor];
  root.style.setProperty("--accent", accent);
  root.style.setProperty("--primary", accent);
  root.style.setProperty("--ring", accent);
  root.style.setProperty("--font-size-base", fontSizeMap[theme.fontSize]);
  root.style.setProperty("--card-radius", radiusMap[theme.borderRadius]);
  root.style.setProperty("--sidebar-width", sidebarWidthMap[theme.sidebarWidth]);
  root.dataset.cardStyle = theme.cardStyle;
  root.dataset.compact = String(theme.compactMode || theme.density === "compact");
  root.dataset.animations = String(theme.animations);
  root.dataset.sidebarStyle = theme.sidebarStyle;
  root.dataset.density = theme.density;

  if (theme.appearance === "light") {
    root.classList.remove("dark");
  } else if (theme.appearance === "dark") {
    root.classList.add("dark");
  } else {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.classList.toggle("dark", prefersDark);
  }
}
