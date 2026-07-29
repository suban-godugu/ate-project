/** Role-based access control helpers for the dashboard. */

export type AppRole = "administrator" | "engineer" | "operator" | "viewer";

const RANK: Record<AppRole, number> = {
  administrator: 0,
  engineer: 1,
  operator: 2,
  viewer: 3,
};

export function roleAtLeast(userRole: string | null | undefined, required: AppRole): boolean {
  if (!userRole) return false;
  const u = RANK[userRole as AppRole];
  const r = RANK[required];
  if (u === undefined || r === undefined) return false;
  return u <= r;
}

/** Nav href → minimum role required to see the link. */
export const ROUTE_ROLES: Record<string, AppRole> = {
  "/overview": "viewer",
  "/upload": "engineer",
  "/datasets": "operator",
  "/patterns": "operator",
  "/failure-rates": "operator",
  "/recurrence": "operator",
  "/correlation": "operator",
  "/die-analysis": "operator",
  "/wafer-analysis": "operator",
  "/fault-prediction": "operator",
  "/reports": "engineer",
  "/history": "operator",
  "/stats": "operator",
  "/users": "administrator",
  "/settings": "administrator",
  "/audit": "administrator",
  "/system-health": "operator",
  "/storage": "engineer",
};

export function canAccessRoute(role: string | null | undefined, href: string): boolean {
  const required = ROUTE_ROLES[href] || "viewer";
  return roleAtLeast(role, required);
}

export function canUpload(role: string | null | undefined) {
  return roleAtLeast(role, "engineer");
}

export function canManageUsers(role: string | null | undefined) {
  return roleAtLeast(role, "administrator");
}
