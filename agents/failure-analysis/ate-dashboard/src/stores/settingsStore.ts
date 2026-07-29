"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AppSettings = {
  backend_url: string;
  polling_interval_ms: number;
  theme: string;
  notification_preferences: {
    analysis_completed: boolean;
    analysis_failed: boolean;
    report_ready: boolean;
    system_warning: boolean;
  };
  export_preferences: { default_format: string };
  analysis_defaults: { async_execution: boolean };
};

const defaults: AppSettings = {
  backend_url: "",
  polling_interval_ms: 2000,
  theme: "enterprise-dark",
  notification_preferences: {
    analysis_completed: true,
    analysis_failed: true,
    report_ready: true,
    system_warning: true,
  },
  export_preferences: { default_format: "pdf" },
  analysis_defaults: { async_execution: true },
};

type SettingsState = {
  settings: AppSettings;
  setSettings: (partial: Partial<AppSettings>) => void;
  replaceSettings: (settings: AppSettings) => void;
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaults,
      setSettings: (partial) =>
        set((s) => ({ settings: { ...s.settings, ...partial } })),
      replaceSettings: (settings) => set({ settings }),
    }),
    { name: "fa-app-settings" },
  ),
);
