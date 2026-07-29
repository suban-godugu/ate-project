"use client";

import { create } from "zustand";

export type AppNotification = {
  id: string;
  title: string;
  body: string;
  category: string;
  read: boolean;
  created_at?: string | null;
};

type NotificationState = {
  items: AppNotification[];
  unreadCount: number;
  open: boolean;
  setItems: (items: AppNotification[], unreadCount: number) => void;
  setOpen: (open: boolean) => void;
  markLocalRead: (id: string) => void;
};

export const useNotificationStore = create<NotificationState>((set) => ({
  items: [],
  unreadCount: 0,
  open: false,
  setItems: (items, unreadCount) => set({ items, unreadCount }),
  setOpen: (open) => set({ open }),
  markLocalRead: (id) =>
    set((s) => ({
      items: s.items.map((n) => (n.id === id ? { ...n, read: true } : n)),
      unreadCount: Math.max(0, s.unreadCount - 1),
    })),
}));
