"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { alertsApi, type AlertCreatePayload, type AlertUpdatePayload } from "@/lib/api/alerts";
import { useUploadStore } from "@/stores/uploadStore";
import { useFilterStore } from "@/stores/filterStore";

export function useAlertMutations() {
  const queryClient = useQueryClient();
  const showToast = useUploadStore((s) => s.showToast);
  const filters = useFilterStore((s) => s.filters);

  const invalidateAlerts = () => {
    queryClient.invalidateQueries({ queryKey: ["dashboard", "alerts"] });
  };

  const createAlert = useMutation({
    mutationFn: (body: AlertCreatePayload) => alertsApi.create(body),
    onSuccess: () => {
      invalidateAlerts();
      showToast("Alert created", "success");
    },
    onError: (err: Error) => {
      showToast(err.message || "Failed to create alert", "error");
    },
  });

  const updateAlert = useMutation({
    mutationFn: ({ id, body }: { id: string; body: AlertUpdatePayload }) => alertsApi.update(id, body),
    onSuccess: () => {
      invalidateAlerts();
      showToast("Alert updated", "success");
    },
    onError: (err: Error) => {
      showToast(err.message || "Failed to update alert", "error");
    },
  });

  const deleteAlert = useMutation({
    mutationFn: (id: string) => alertsApi.remove(id),
    onSuccess: () => {
      invalidateAlerts();
      showToast("Alert deleted", "success");
    },
    onError: (err: Error) => {
      showToast(err.message || "Failed to delete alert", "error");
    },
  });

  return {
    filters,
    createAlert,
    updateAlert,
    deleteAlert,
  };
}
