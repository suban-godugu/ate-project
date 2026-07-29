/** Centralized frontend logger for errors, API failures, and analysis events. */

import { appConfig } from "@/lib/config";

type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
};

function shouldLog(level: LogLevel) {
  return LEVEL_ORDER[level] >= LEVEL_ORDER[appConfig.logLevel];
}

function normalizeMeta(meta?: Record<string, unknown>) {
  if (!meta) return undefined;
  return Object.fromEntries(
    Object.entries(meta).map(([key, value]) => [
      key,
      value instanceof Error
        ? {
            name: value.name,
            message: value.message,
            stack: value.stack,
          }
        : value,
    ]),
  );
}

function emit(level: LogLevel, message: string, meta?: Record<string, unknown>) {
  if (!shouldLog(level)) return;
  const normalizedMeta = normalizeMeta(meta);
  const entry = {
    ts: new Date().toISOString(),
    level,
    message,
    ...(normalizedMeta || {}),
  };
  const line = `[FA] ${message}`;
  if (level === "error") console.error(line, normalizedMeta || {});
  else if (level === "warn") console.warn(line, normalizedMeta || {});
  else console.info(line, normalizedMeta || {});

  if (typeof window !== "undefined") {
    try {
      const key = "fa-client-logs";
      const prev = JSON.parse(sessionStorage.getItem(key) || "[]") as unknown[];
      sessionStorage.setItem(key, JSON.stringify([...prev.slice(-99), entry]));
    } catch {
      /* ignore quota */
    }
  }
}

export const logger = {
  debug: (message: string, meta?: Record<string, unknown>) => emit("debug", message, meta),
  info: (message: string, meta?: Record<string, unknown>) => emit("info", message, meta),
  warn: (message: string, meta?: Record<string, unknown>) => emit("warn", message, meta),
  error: (message: string, meta?: Record<string, unknown>) => emit("error", message, meta),
  route: (path: string) => emit("info", "route_change", { path }),
  apiError: (url: string, status: number, detail?: string) =>
    emit("warn", "api_error", { url, status, detail }),
  analysis: (event: string, meta?: Record<string, unknown>) =>
    emit("info", "analysis_event", { event, ...meta }),
};
