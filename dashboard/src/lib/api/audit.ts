import { apiFetch } from "./client";

export interface AuditLogItem {
  id: string;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  user_id?: string | null;
  username?: string | null;
  severity: string;
  status?: string | null;
  message?: string | null;
  upload_job_id?: string | null;
  filename?: string | null;
  created_at?: string | null;
  meta?: Record<string, unknown>;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface AuditQueryParams {
  page?: number;
  page_size?: number;
  action?: string;
  entity_type?: string;
  severity?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  user_id?: string;
}

export async function getAuditLogs(params: AuditQueryParams = {}): Promise<AuditLogListResponse> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") qs.set(key, String(value));
  }
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<AuditLogListResponse>(`/audit${suffix}`);
}

export const auditApi = { getAuditLogs };
