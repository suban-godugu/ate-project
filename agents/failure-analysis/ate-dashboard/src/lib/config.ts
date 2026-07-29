/** Central frontend configuration from environment variables. */

const embedBasePath = process.env.NEXT_PUBLIC_EMBED_BASE_PATH || "";

export const appConfig = {
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL || `${embedBasePath}/api/v1`,
  appName: process.env.NEXT_PUBLIC_APP_NAME || "ATE Dashboard",
  authEnabled: process.env.NEXT_PUBLIC_AUTH_ENABLED === "true",
  defaultPollingMs: Number(process.env.NEXT_PUBLIC_POLLING_INTERVAL_MS || 2000),
  logLevel: (process.env.NEXT_PUBLIC_LOG_LEVEL || "info") as
    | "debug"
    | "info"
    | "warn"
    | "error",
} as const;
