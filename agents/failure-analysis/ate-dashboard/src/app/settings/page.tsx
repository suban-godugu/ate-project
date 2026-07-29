"use client";

import { useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSettingsStore, type AppSettings } from "@/stores/settingsStore";
import { notify } from "@/stores/toastStore";

export default function SettingsPage() {
  const settings = useSettingsStore((s) => s.settings);
  const setSettings = useSettingsStore((s) => s.setSettings);
  const replaceSettings = useSettingsStore((s) => s.replaceSettings);

  const { data } = useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const { data } = await api.get("/settings");
      return data.settings as AppSettings;
    },
  });

  useEffect(() => {
    if (data) replaceSettings(data);
  }, [data, replaceSettings]);

  const save = useMutation({
    mutationFn: async () => {
      const { data } = await api.put("/settings", settings);
      return data.settings as AppSettings;
    },
    onSuccess: (saved) => {
      replaceSettings(saved);
      notify({ title: "Settings Saved", variant: "success" });
    },
    onError: () => notify({ title: "Save Failed", variant: "error" }),
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Application Settings</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Backend URL, polling, theme, notifications, export, and analysis defaults.
        </p>
      </header>

      <div className="glass-panel grid gap-4 rounded-2xl p-6 md:grid-cols-2" data-testid="settings-form">
        <label className="block text-sm">
          <span className="text-[var(--muted)]">Backend URL</span>
          <input
            value={settings.backend_url}
            onChange={(e) => setSettings({ backend_url: e.target.value })}
            placeholder="/api/v1 or https://api.example.com/api/v1"
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="text-[var(--muted)]">Polling Interval (ms)</span>
          <input
            type="number"
            min={1000}
            max={60000}
            value={settings.polling_interval_ms}
            onChange={(e) =>
              setSettings({ polling_interval_ms: Number(e.target.value) || 2000 })
            }
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="text-[var(--muted)]">Theme</span>
          <select
            value={settings.theme}
            onChange={(e) => setSettings({ theme: e.target.value })}
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2"
          >
            <option value="enterprise-dark">Enterprise Dark Glass</option>
          </select>
        </label>
        <label className="block text-sm">
          <span className="text-[var(--muted)]">Default Export Format</span>
          <select
            value={settings.export_preferences.default_format}
            onChange={(e) =>
              setSettings({
                export_preferences: { default_format: e.target.value },
              })
            }
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2"
          >
            {["pdf", "csv", "xlsx", "json", "html"].map((f) => (
              <option key={f} value={f}>
                {f.toUpperCase()}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="md:col-span-2">
          <legend className="text-sm text-[var(--muted)]">Notification Preferences</legend>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {(
              [
                ["analysis_completed", "Analysis Completed"],
                ["analysis_failed", "Analysis Failed"],
                ["report_ready", "Report Ready"],
                ["system_warning", "System Warning"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={settings.notification_preferences[key]}
                  onChange={(e) =>
                    setSettings({
                      notification_preferences: {
                        ...settings.notification_preferences,
                        [key]: e.target.checked,
                      },
                    })
                  }
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        <label className="flex items-center gap-2 text-sm md:col-span-2">
          <input
            type="checkbox"
            checked={settings.analysis_defaults.async_execution}
            onChange={(e) =>
              setSettings({
                analysis_defaults: { async_execution: e.target.checked },
              })
            }
          />
          Async analysis execution by default
        </label>
      </div>

      <button
        type="button"
        onClick={() => save.mutate()}
        disabled={save.isPending}
        className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white"
      >
        {save.isPending ? "Saving…" : "Save Settings"}
      </button>
    </div>
  );
}
