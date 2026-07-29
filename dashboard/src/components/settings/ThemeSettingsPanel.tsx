"use client";

import { motion } from "framer-motion";
import { RotateCcw } from "lucide-react";
import { SegmentedControl } from "@/components/settings/SegmentedControl";
import {
  SettingsRow,
  SettingsSection,
} from "@/components/settings/SettingsSection";
import { ThemePreview } from "@/components/settings/ThemePreview";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/contexts/ThemeContext";
import {
  accentColors,
  themePresets,
  type Appearance,
  type BorderRadius,
  type CardStyle,
  type Density,
  type FontSize,
  type SidebarStyle,
  type SidebarWidth,
} from "@/types/theme";

const FONT_SIZES: FontSize[] = ["small", "medium", "large"];
const FONT_LABELS = ["Small", "Medium", "Large"];

export function ThemeSettingsPanel() {
  const { theme, updateTheme, resetTheme, accentHex } = useTheme();

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      className="settings-panel glass-card gradient-border hover-lift p-8"
    >
      <div className="mb-8">
        <h2 className="text-xl font-bold text-white">Theme Settings</h2>
        <p className="mt-1 text-sm text-slate-400">
          Customize the appearance of your workspace.
        </p>
      </div>

      <div className="space-y-8">
        {/* Theme Presets */}
        <SettingsSection title="Theme Presets" description="One-click professional themes">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {themePresets.map((preset) => (
              <motion.button
                key={preset.id}
                type="button"
                whileHover={{ scale: 1.03, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => updateTheme(preset.config)}
                className="rounded-xl border border-[#2D3748] bg-[#0A1020]/60 p-3 text-left transition-shadow hover:border-[#7C3AED]/50 hover:shadow-lg hover:shadow-purple-500/10"
              >
                <div
                  className="mb-2 h-6 w-6 rounded-full"
                  style={{
                    backgroundColor:
                      accentColors.find((c) => c.id === preset.config.primaryColor)
                        ?.hex ?? "#7C3AED",
                  }}
                />
                <p className="text-xs font-semibold text-white">{preset.name}</p>
                <p className="text-[10px] text-slate-500">{preset.description}</p>
              </motion.button>
            ))}
          </div>
        </SettingsSection>

        {/* Appearance + Accent */}
        <div className="grid gap-8 md:grid-cols-2">
          <SettingsSection title="Appearance" divider={false}>
            <RadioGroup
              value={theme.appearance}
              onValueChange={(v) => updateTheme({ appearance: v as Appearance })}
              className="space-y-3"
            >
              {(
                [
                  ["dark", "Dark Mode"],
                  ["light", "Light Mode"],
                  ["system", "System Default"],
                ] as const
              ).map(([val, label]) => (
                <div key={val} className="flex items-center gap-3">
                  <RadioGroupItem value={val} id={`app-${val}`} />
                  <Label htmlFor={`app-${val}`} className="text-sm text-slate-300">
                    {label}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </SettingsSection>

          <SettingsSection title="Accent Color" divider={false}>
            <div className="flex flex-wrap gap-4">
              {accentColors.map((c) => {
                const selected = theme.primaryColor === c.id;
                return (
                  <motion.button
                    key={c.id}
                    type="button"
                    title={c.label}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => updateTheme({ primaryColor: c.id })}
                    className="relative flex flex-col items-center gap-1.5"
                  >
                    <div
                      className="h-10 w-10 rounded-full"
                      style={{ backgroundColor: c.hex }}
                    />
                    {selected && (
                      <motion.span
                        layoutId="accent-ring"
                        className="absolute -inset-1 rounded-full border-2"
                        style={{
                          borderColor: c.hex,
                          boxShadow: `0 0 16px ${c.hex}80`,
                        }}
                        transition={{ type: "spring", bounce: 0.2 }}
                      />
                    )}
                    <span className="text-[10px] text-slate-500">{c.label}</span>
                  </motion.button>
                );
              })}
            </div>
          </SettingsSection>
        </div>

        <div className="h-px bg-gradient-to-r from-transparent via-[#2D3748] to-transparent" />

        {/* Layout */}
        <SettingsSection title="Layout">
          <div className="space-y-5">
            <SettingsRow label="Sidebar Style">
              <SegmentedControl<SidebarStyle>
                accentColor={accentHex}
                value={theme.sidebarStyle}
                onChange={(v) => updateTheme({ sidebarStyle: v })}
                options={[
                  { value: "default", label: "Default" },
                  { value: "compact", label: "Compact" },
                  { value: "floating", label: "Floating" },
                ]}
              />
            </SettingsRow>

            <SettingsRow label="Sidebar Width">
              <SegmentedControl<SidebarWidth>
                accentColor={accentHex}
                value={theme.sidebarWidth}
                onChange={(v) => updateTheme({ sidebarWidth: v })}
                options={[
                  { value: "compact", label: "Compact" },
                  { value: "standard", label: "Standard" },
                  { value: "expanded", label: "Expanded" },
                ]}
              />
            </SettingsRow>

            <SettingsRow label="Card Style">
              <SegmentedControl<CardStyle>
                accentColor={accentHex}
                value={theme.cardStyle}
                onChange={(v) => updateTheme({ cardStyle: v })}
                options={[
                  { value: "glass", label: "Glass" },
                  { value: "solid", label: "Solid" },
                  { value: "minimal", label: "Minimal" },
                ]}
              />
            </SettingsRow>

            <SettingsRow label="Corner Radius">
              <SegmentedControl<BorderRadius>
                accentColor={accentHex}
                value={theme.borderRadius}
                onChange={(v) => updateTheme({ borderRadius: v })}
                options={[
                  { value: "small", label: "Small" },
                  { value: "medium", label: "Medium" },
                  { value: "large", label: "Large" },
                ]}
              />
            </SettingsRow>

            <SettingsRow label="Navigation Density">
              <SegmentedControl<Density>
                accentColor={accentHex}
                value={theme.density}
                onChange={(v) => updateTheme({ density: v, compactMode: v === "compact" })}
                options={[
                  { value: "comfortable", label: "Comfortable" },
                  { value: "compact", label: "Compact" },
                ]}
              />
            </SettingsRow>
          </div>
        </SettingsSection>

        {/* Typography */}
        <SettingsSection title="Typography">
          <SettingsRow label="Font Size">
            <div className="w-full max-w-xs space-y-2">
              <Slider
                value={[FONT_SIZES.indexOf(theme.fontSize)]}
                onValueChange={(v) => {
                  const idx = Array.isArray(v) ? v[0] : v;
                  if (idx !== undefined) updateTheme({ fontSize: FONT_SIZES[idx] });
                }}
                min={0}
                max={2}
                step={1}
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                {FONT_LABELS.map((l) => (
                  <span key={l}>{l}</span>
                ))}
              </div>
            </div>
          </SettingsRow>
        </SettingsSection>

        {/* Toggles */}
        <SettingsSection title="Behavior" divider={false}>
          <div className="space-y-4">
            <SettingsRow label="Animations">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  {theme.animations ? "ON" : "OFF"}
                </span>
                <Switch
                  checked={theme.animations}
                  onCheckedChange={(v) => updateTheme({ animations: v })}
                />
              </div>
            </SettingsRow>
            <SettingsRow label="Compact Mode">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  {theme.compactMode ? "ON" : "OFF"}
                </span>
                <Switch
                  checked={theme.compactMode}
                  onCheckedChange={(v) => updateTheme({ compactMode: v })}
                />
              </div>
            </SettingsRow>
          </div>
        </SettingsSection>

        <div className="h-px bg-gradient-to-r from-transparent via-[#2D3748] to-transparent" />

        {/* Live Preview */}
        <ThemePreview theme={theme} />

        {/* Reset */}
        <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
          <Button
            variant="outline"
            className="w-full rounded-xl border-[#2D3748] py-5 text-sm hover:border-[#7C3AED] hover:bg-[#7C3AED]/5"
            onClick={resetTheme}
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset Theme
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}
