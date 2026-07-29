import { apiFetch } from "@/lib/api/client";
import type { AlertModule, AlertStatus, RecentAlertRow, Severity } from "@/types/alerts";

export interface AlertCreatePayload {
  source_module: string;
  severity: string;
  status?: string;
  title?: string | null;
  description?: string | null;
  lot_id?: string | null;
  wafer_id?: string | null;
  assigned_user_id?: string | null;
}

export interface AlertUpdatePayload {
  severity?: string;
  status?: string;
  title?: string | null;
  description?: string | null;
  assigned_user_id?: string | null;
}

export const ALERT_MODULES: AlertModule[] = [
  "Scan Chain",
  "MBIST",
  "LBIST",
  "Wafer",
  "Cost",
  "AI Recommendation",
];

export const ALERT_SEVERITIES: Severity[] = ["Critical", "High", "Medium", "Low"];

export const ALERT_STATUSES: AlertStatus[] = ["Open", "Investigating", "Resolved", "Closed", "Pending"];

export const alertsApi = {
  create(body: AlertCreatePayload): Promise<RecentAlertRow> {
    return apiFetch<RecentAlertRow>("/dashboard/alerts", { method: "POST", body });
  },
  update(id: string, body: AlertUpdatePayload): Promise<RecentAlertRow> {
    return apiFetch<RecentAlertRow>(`/dashboard/alerts/${id}`, { method: "PATCH", body });
  },
  remove(id: string): Promise<{ ok: boolean }> {
    return apiFetch<{ ok: boolean }>(`/dashboard/alerts/${id}`, { method: "DELETE" });
  },
};
