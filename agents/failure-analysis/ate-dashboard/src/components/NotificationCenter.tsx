"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { useNotificationStore } from "@/stores/notificationStore";
import { appConfig } from "@/lib/config";

export function NotificationCenter() {
  const open = useNotificationStore((s) => s.open);
  const setOpen = useNotificationStore((s) => s.setOpen);
  const setItems = useNotificationStore((s) => s.setItems);
  const markLocalRead = useNotificationStore((s) => s.markLocalRead);
  const items = useNotificationStore((s) => s.items);
  const accessToken = useAuthStore((s) => s.accessToken);

  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const { data } = await api.get("/notifications");
      return data as {
        unread_count: number;
        notifications: Array<{
          id: string;
          title: string;
          body: string;
          category: string;
          read: boolean;
          created_at?: string | null;
        }>;
      };
    },
    enabled: Boolean(accessToken) && appConfig.authEnabled,
    refetchInterval: 15_000,
  });

  useEffect(() => {
    if (data) setItems(data.notifications || [], data.unread_count || 0);
  }, [data, setItems]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-y-0 right-0 z-50 w-full max-w-md border-l border-white/10 bg-[var(--surface)]/95 p-4 shadow-2xl backdrop-blur-xl"
      role="dialog"
      aria-label="Notification center"
    >
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Notifications
        </h2>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-lg p-2 hover:bg-white/10"
          aria-label="Close notifications"
        >
          <X size={16} />
        </button>
      </div>
      <ul className="space-y-2 overflow-auto" style={{ maxHeight: "calc(100vh - 6rem)" }}>
        {!items.length && (
          <li className="text-sm text-[var(--muted)]">No notifications yet.</li>
        )}
        {items.map((n) => (
          <li
            key={n.id}
            className={`rounded-xl border border-white/10 p-3 ${n.read ? "opacity-60" : "bg-white/5"}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="text-sm font-medium">{n.title}</div>
                <div className="mt-1 text-xs text-[var(--muted)]">{n.body}</div>
                <div className="mt-1 text-[10px] uppercase text-[var(--accent)]">
                  {n.category}
                </div>
              </div>
              {!n.read && (
                <button
                  type="button"
                  className="text-xs text-[var(--accent)] hover:underline"
                  onClick={async () => {
                    markLocalRead(n.id);
                    try {
                      await api.post(`/notifications/${n.id}/read`);
                    } catch {
                      /* ignore */
                    }
                  }}
                >
                  Mark read
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
