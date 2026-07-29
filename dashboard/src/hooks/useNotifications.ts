"use client";

import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isLiveApi } from "@/lib/api/config";
import { notificationsApi } from "@/lib/api/notifications";
import { useNotificationStore } from "@/stores/notificationStore";
import type { PlatformNotification } from "@/types/platform";

const seedNotifications: PlatformNotification[] = [];

export function useNotifications() {
  const queryClient = useQueryClient();
  const mockNotifications = useNotificationStore((s) => s.notifications);
  const mockMarkRead = useNotificationStore((s) => s.markRead);
  const mockMarkAllRead = useNotificationStore((s) => s.markAllRead);

  const liveQuery = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsApi.listNotifications,
    enabled: isLiveApi(),
    initialData: seedNotifications,
  });

  const markReadMutation = useMutation({
    mutationFn: notificationsApi.markNotificationRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllMutation = useMutation({
    mutationFn: notificationsApi.markAllNotificationsRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const notifications: PlatformNotification[] = isLiveApi()
    ? (liveQuery.data ?? [])
    : mockNotifications;

  const markRead = useCallback(
    (id: string) => {
      if (isLiveApi()) markReadMutation.mutate(id);
      else mockMarkRead(id);
    },
    [markReadMutation, mockMarkRead]
  );

  const markAllRead = useCallback(() => {
    if (isLiveApi()) markAllMutation.mutate();
    else mockMarkAllRead();
  }, [markAllMutation, mockMarkAllRead]);

  return {
    notifications,
    markRead,
    markAllRead,
    isLoading: isLiveApi() ? liveQuery.isLoading : false,
    unreadCount: notifications.filter((n) => !n.read).length,
  };
}
