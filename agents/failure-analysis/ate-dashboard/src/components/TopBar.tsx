"use client";

import Link from "next/link";
import { Bell, LogOut, User } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { useNotificationStore } from "@/stores/notificationStore";
import { logoutRequest } from "@/services/auth";
import { useRouter } from "next/navigation";
import { notify } from "@/stores/toastStore";

export function TopBar() {
  const user = useAuthStore((s) => s.user);
  const clearSession = useAuthStore((s) => s.clearSession);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const unread = useNotificationStore((s) => s.unreadCount);
  const setOpen = useNotificationStore((s) => s.setOpen);
  const router = useRouter();

  async function logout() {
    try {
      await logoutRequest(refreshToken);
    } catch {
      /* still clear local session */
    }
    clearSession();
    document.cookie = "fa_session=; path=/; Max-Age=0";
    notify({ title: "Signed out", variant: "info" });
    router.replace("/login");
  }

  return (
    <header
      className="glass-panel flex items-center justify-between rounded-2xl px-4 py-3"
      role="banner"
    >
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:rounded focus:bg-white focus:px-2 focus:py-1 focus:text-black">
        Skip to main content
      </a>
      <div className="text-sm text-[var(--muted)]">
        Failure Analysis Workbench
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="relative rounded-xl border border-white/10 p-2 hover:bg-white/5"
          aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}
        >
          <Bell size={16} />
          {unread > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--accent)] px-1 text-[10px] text-white">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </button>
        {user && (
          <div className="hidden items-center gap-2 rounded-xl border border-white/10 px-3 py-1.5 text-xs sm:flex">
            <User size={14} aria-hidden />
            <span>{user.full_name || user.email}</span>
            <span className="text-[var(--muted)]">· {user.role}</span>
          </div>
        )}
        <button
          type="button"
          onClick={logout}
          className="inline-flex items-center gap-1 rounded-xl border border-white/10 px-3 py-1.5 text-xs hover:bg-white/5"
          aria-label="Sign out"
        >
          <LogOut size={14} />
          Sign out
        </button>
        <Link href="/settings" className="sr-only">
          Settings
        </Link>
      </div>
    </header>
  );
}
