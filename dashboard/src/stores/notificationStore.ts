import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PlatformNotification } from "@/types/platform";

const seedNotifications: PlatformNotification[] = [
  {
    id: "n1",
    title: "Critical Scan Chain Failure",
    message: "SC-4821 pattern failure detected on LOT-4821",
    severity: "critical",
    read: false,
    timestamp: "2 min ago",
    alertRoute: "/dashboard/alerts",
  },
  {
    id: "n2",
    title: "MBIST Repair Threshold",
    message: "SRAM Bank-2 repair failure threshold exceeded",
    severity: "critical",
    read: false,
    timestamp: "8 min ago",
    alertRoute: "/dashboard/alerts",
  },
  {
    id: "n3",
    title: "Yield Drop Warning",
    message: "Wafer W-08 yield below 90% on edge dies",
    severity: "warning",
    read: false,
    timestamp: "15 min ago",
    alertRoute: "/dashboard/alerts",
  },
  {
    id: "n4",
    title: "Cost Budget Alert",
    message: "Test cost exceeded budget threshold by 12%",
    severity: "warning",
    read: true,
    timestamp: "35 min ago",
    alertRoute: "/dashboard/cost-intelligence",
  },
  {
    id: "n5",
    title: "AI Recommendation Ready",
    message: "12 new optimization recommendations available",
    severity: "info",
    read: false,
    timestamp: "48 min ago",
    alertRoute: "/dashboard/recommendation-analysis",
  },
  {
    id: "n6",
    title: "System Maintenance",
    message: "Scheduled maintenance window tonight 02:00–04:00 IST",
    severity: "system",
    read: true,
    timestamp: "1 hr ago",
  },
];

interface NotificationStore {
  notifications: PlatformNotification[];
  markRead: (id: string) => void;
  markAllRead: () => void;
  unreadCount: () => number;
}

export const useNotificationStore = create<NotificationStore>()(
  persist(
    (set, get) => ({
      notifications: seedNotifications,
      markRead: (id) =>
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n
          ),
        })),
      markAllRead: () =>
        set((state) => ({
          notifications: state.notifications.map((n) => ({ ...n, read: true })),
        })),
      unreadCount: () => get().notifications.filter((n) => !n.read).length,
    }),
    { name: "ate-notifications" }
  )
);
