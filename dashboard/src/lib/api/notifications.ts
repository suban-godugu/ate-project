import type { PlatformNotification } from "@/types/platform";
import { apiFetch } from "./client";

export async function listNotifications(): Promise<PlatformNotification[]> {
  return apiFetch("/notifications");
}

export async function markNotificationRead(id: string): Promise<void> {
  await apiFetch(`/notifications/${id}/read`, { method: "PATCH" });
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiFetch("/notifications/read-all", { method: "PATCH" });
}

export const notificationsApi = {
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
};
