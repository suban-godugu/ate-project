"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { AccountPresetsPanel } from "@/components/settings/AccountPresetsPanel";
import { SettingsToast } from "@/components/settings/SettingsToast";
import { ThemeSettingsPanel } from "@/components/settings/ThemeSettingsPanel";
import { RecentActivityPanel } from "@/components/settings/RecentActivityPanel";
import { authApi } from "@/lib/api/auth";
import { isLiveApi } from "@/lib/api/config";
import { useUserStore } from "@/stores/userStore";
import { defaultAccountPreset, type AccountPreset } from "@/types/theme";

export default function SettingsPage() {
  const storedProfile = useUserStore((s) => s.profile);
  const updateProfile = useUserStore((s) => s.updateProfile);
  const [account, setAccount] = useState<AccountPreset>(storedProfile);
  const [savedAccount, setSavedAccount] = useState<AccountPreset>(storedProfile);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);

  useEffect(() => {
    setAccount(storedProfile);
    setSavedAccount(storedProfile);
  }, [storedProfile]);

  useEffect(() => {
    if (!isLiveApi()) return;
    authApi
      .getPreferences()
      .then((prefs) => {
        if (prefs.account_json && typeof prefs.account_json === "object") {
          const loaded = {
            ...storedProfile,
            ...(prefs.account_json as unknown as AccountPreset),
          };
          setAccount(loaded);
          setSavedAccount(loaded);
          updateProfile(loaded);
        }
      })
      .catch(() => {
        /* keep local profile */
      });
  }, [storedProfile, updateProfile]);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      if (isLiveApi()) {
        await authApi.updatePreferences({
          account_json: account as unknown as Record<string, unknown>,
        });
      } else {
        await new Promise((r) => setTimeout(r, 400));
      }
      updateProfile(account);
      setSavedAccount(account);
      setSaveSuccess(true);
      setToastVisible(true);
    } finally {
      setIsSaving(false);
      setTimeout(() => {
        setSaveSuccess(false);
        setToastVisible(false);
      }, 3000);
    }
  }, [account, updateProfile]);

  const handleCancel = () => setAccount(savedAccount);

  return (
    <DashboardLayout title="Settings" hideQuickFilters pageId="settings">
      <div className="settings-page mx-auto max-w-[1600px]">
        <motion.header
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 border-b border-[#2D3748]/60 pb-8"
        >
          <h1 className="text-3xl font-bold tracking-tight text-white">Settings</h1>
          <p className="mt-2 text-base text-slate-400">
            Manage workspace appearance and account preferences.
          </p>
        </motion.header>

        <div className="settings-split">
          <ThemeSettingsPanel />
          <AccountPresetsPanel
            account={account}
            onChange={setAccount}
            onSave={handleSave}
            onCancel={handleCancel}
            isSaving={isSaving}
            saveSuccess={saveSuccess}
          />
        </div>

        <RecentActivityPanel />
      </div>

      <SettingsToast
        message="Settings updated successfully"
        visible={toastVisible}
        onClose={() => setToastVisible(false)}
      />
    </DashboardLayout>
  );
}
