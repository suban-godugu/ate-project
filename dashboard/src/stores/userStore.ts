"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { defaultAccountPreset } from "@/types/theme";
import type { UserProfile } from "@/types/platform";
import { setAccessToken } from "@/lib/api/config";
import type { AuthUser } from "@/lib/api/auth";

const defaultProfile: UserProfile = {
  ...defaultAccountPreset,
  avatarInitials: "AJ",
  password: "",
};

interface UserStore {
  profile: UserProfile;
  session: AuthUser | null;
  isAuthenticated: boolean;
  updateProfile: (partial: Partial<UserProfile>) => void;
  resetProfile: () => void;
  setSession: (user: AuthUser, accessToken: string) => void;
  clearSession: () => void;
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      profile: defaultProfile,
      session: null,
      isAuthenticated: false,
      updateProfile: (partial) =>
        set((state) => ({
          profile: {
            ...state.profile,
            ...partial,
            avatarInitials:
              partial.name
                ? partial.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()
                : state.profile.avatarInitials,
          },
        })),
      resetProfile: () => set({ profile: defaultProfile }),
      setSession: (user, accessToken) => {
        setAccessToken(accessToken);
        set({
          session: user,
          isAuthenticated: true,
          profile: {
            ...defaultProfile,
            name: user.name,
            email: user.email,
            avatarInitials: user.name
              .split(" ")
              .map((n) => n[0])
              .join("")
              .slice(0, 2)
              .toUpperCase(),
          },
        });
      },
      clearSession: () => {
        setAccessToken(null);
        set({ session: null, isAuthenticated: false });
      },
    }),
    {
      name: "ate-user-profile",
      partialize: (state) => ({
        profile: state.profile,
        session: state.session,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export function useSessionUserName(): string {
  return useUserStore((s) => s.session?.name ?? s.profile.name);
}
