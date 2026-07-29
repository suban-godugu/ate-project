"use client";

import { motion } from "framer-motion";
import { Building2, Clock, Upload } from "lucide-react";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/contexts/ThemeContext";
import type { AccountPreset, DateFormat, NumberFormat } from "@/types/theme";

interface AccountPresetsPanelProps {
  account: AccountPreset;
  onChange: (account: AccountPreset) => void;
  onSave: () => void;
  onCancel: () => void;
  isSaving: boolean;
  saveSuccess: boolean;
}

const inputClass =
  "rounded-xl border-[#2D3748] bg-[#0A1020]/80 backdrop-blur-sm focus-visible:border-[#7C3AED] focus-visible:ring-[#7C3AED]/30";

export function AccountPresetsPanel({
  account,
  onChange,
  onSave,
  onCancel,
  isSaving,
  saveSuccess,
}: AccountPresetsPanelProps) {
  const { accentHex } = useTheme();
  const initials = account.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2);

  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="settings-panel glass-card gradient-border hover-lift flex flex-col p-8"
    >
      <div className="mb-6">
        <h2 className="text-xl font-bold text-white">Account Presets</h2>
        <p className="mt-1 text-sm text-slate-400">Manage profile preferences.</p>
      </div>

      {/* Profile Summary */}
      <div
        className="mb-8 rounded-2xl border border-[#2D3748]/60 p-5"
        style={{ background: `linear-gradient(135deg, ${accentHex}15, transparent)` }}
      >
        <div className="flex items-center gap-4">
          <Avatar
            className="h-16 w-16 ring-2 ring-offset-2 ring-offset-[#111827]"
            style={{ boxShadow: `0 0 0 2px ${accentHex}` }}
          >
            <AvatarFallback
              className="text-lg font-bold text-white"
              style={{ backgroundColor: accentHex }}
            >
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold text-white">{account.name}</p>
            <p className="text-sm text-slate-400">
              {account.role} · {account.department}
            </p>
            <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-500">
              <span className="flex items-center gap-1">
                <Building2 className="h-3 w-3" />
                {account.organization}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {account.lastLogin}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-8">
        {/* Avatar */}
        <SettingsSection title="Avatar" divider={false}>
          <div className="flex items-center gap-4">
            <Avatar className="h-20 w-20">
              <AvatarFallback
                className="text-xl text-white"
                style={{ backgroundColor: accentHex }}
              >
                {initials}
              </AvatarFallback>
            </Avatar>
            <Button
              variant="outline"
              size="sm"
              className="rounded-xl border-[#2D3748] hover:border-[#7C3AED]"
            >
              <Upload className="mr-2 h-3.5 w-3.5" />
              Upload
            </Button>
          </div>
        </SettingsSection>

        <div className="h-px bg-gradient-to-r from-transparent via-[#2D3748] to-transparent" />

        {/* Profile */}
        <SettingsSection title="Profile">
          <div className="space-y-4">
            {(
              [
                ["name", "Name", "text"],
                ["email", "Email", "email"],
              ] as const
            ).map(([key, label, type]) => (
              <div key={key}>
                <Label className="mb-1.5 block text-xs text-slate-400">{label}</Label>
                <Input
                  type={type}
                  value={account[key]}
                  onChange={(e) => onChange({ ...account, [key]: e.target.value })}
                  className={inputClass}
                />
              </div>
            ))}

            <div>
              <Label className="mb-1.5 block text-xs text-slate-400">Role</Label>
              <Select
                value={account.role}
                onValueChange={(v) => onChange({ ...account, role: v ?? account.role })}
              >
                <SelectTrigger className={inputClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["Admin", "Manager", "Engineer", "Viewer"].map((r) => (
                    <SelectItem key={r} value={r}>{r}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="mb-1.5 block text-xs text-slate-400">Department</Label>
              <Select
                value={account.department}
                onValueChange={(v) =>
                  onChange({ ...account, department: v ?? account.department })
                }
              >
                <SelectTrigger className={inputClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[
                    "ATE Engineering",
                    "Yield Engineering",
                    "Manufacturing",
                    "Quality",
                    "AI Research",
                  ].map((d) => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </SettingsSection>

        {/* Preferences */}
        <SettingsSection title="Preferences">
          <div className="space-y-4">
            <div>
              <Label className="mb-1.5 block text-xs text-slate-400">Default Dashboard</Label>
              <Select
                value={account.defaultDashboard}
                onValueChange={(v) =>
                  onChange({ ...account, defaultDashboard: v ?? account.defaultDashboard })
                }
              >
                <SelectTrigger className={inputClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[
                    "Executive Dashboard",
                    "Wafer Analytics",
                    "Pattern Analysis",
                    "Cost Intelligence",
                  ].map((d) => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="mb-1.5 block text-xs text-slate-400">Language</Label>
              <Select
                value={account.language}
                onValueChange={(v) =>
                  onChange({ ...account, language: v ?? account.language })
                }
              >
                <SelectTrigger className={inputClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["English", "Japanese", "Chinese", "German"].map((l) => (
                    <SelectItem key={l} value={l}>{l}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="mb-1.5 block text-xs text-slate-400">Timezone</Label>
              <Select
                value={account.timezone}
                onValueChange={(v) =>
                  onChange({ ...account, timezone: v ?? account.timezone })
                }
              >
                <SelectTrigger className={inputClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="UTC">UTC</SelectItem>
                  <SelectItem value="Asia/Kolkata">IST</SelectItem>
                  <SelectItem value="America/Los_Angeles">PST</SelectItem>
                  <SelectItem value="Europe/Berlin">CET</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="mb-1.5 block text-xs text-slate-400">Date Format</Label>
              <Select
                value={account.dateFormat}
                onValueChange={(v) =>
                  onChange({ ...account, dateFormat: (v as DateFormat) ?? account.dateFormat })
                }
              >
                <SelectTrigger className={inputClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                  <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                  <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="mb-1.5 block text-xs text-slate-400">Number Format</Label>
              <Select
                value={account.numberFormat}
                onValueChange={(v) =>
                  onChange({
                    ...account,
                    numberFormat: (v as NumberFormat) ?? account.numberFormat,
                  })
                }
              >
                <SelectTrigger className={inputClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="US">US (1,234.56)</SelectItem>
                  <SelectItem value="EU">EU (1.234,56)</SelectItem>
                  <SelectItem value="IN">IN (1,23,456.78)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </SettingsSection>

        {/* Notifications */}
        <SettingsSection title="Notifications" divider={false}>
          <div className="space-y-4 rounded-xl border border-[#2D3748]/50 bg-[#0A1020]/40 p-4">
            {(
              [
                ["email", "Email"],
                ["desktop", "Desktop"],
                ["push", "Push"],
              ] as const
            ).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between">
                <Label className="text-sm text-slate-300">{label}</Label>
                <Switch
                  checked={account.notifications[key]}
                  onCheckedChange={(v) =>
                    onChange({
                      ...account,
                      notifications: { ...account.notifications, [key]: v },
                    })
                  }
                />
              </div>
            ))}
          </div>
        </SettingsSection>
      </div>

      {/* Actions */}
      <div className="mt-8 flex gap-3 border-t border-[#2D3748]/60 pt-6">
        <Button
          variant="outline"
          className="flex-1 rounded-xl border-[#2D3748] py-5"
          onClick={onCancel}
          disabled={isSaving}
        >
          Cancel
        </Button>
        <motion.div className="flex-1" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
          <Button
            className="btn-glow w-full rounded-xl py-5 font-semibold text-white"
            style={{
              background: saveSuccess
                ? "linear-gradient(135deg, #059669, #047857)"
                : `linear-gradient(135deg, ${accentHex}, #6D28D9)`,
            }}
            onClick={onSave}
            disabled={isSaving}
          >
            {isSaving ? (
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
                className="mr-2 inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent"
              />
            ) : null}
            {saveSuccess ? "Saved!" : isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}
