import { describe, expect, it } from "vitest";
import { canAccessRoute, roleAtLeast } from "@/lib/rbac";
import { friendlyApiError } from "@/services/auth";

describe("RBAC", () => {
  it("ranks administrator above viewer", () => {
    expect(roleAtLeast("administrator", "viewer")).toBe(true);
    expect(roleAtLeast("viewer", "administrator")).toBe(false);
  });

  it("restricts admin-only routes", () => {
    expect(canAccessRoute("viewer", "/users")).toBe(false);
    expect(canAccessRoute("administrator", "/users")).toBe(true);
    expect(canAccessRoute("engineer", "/upload")).toBe(true);
    expect(canAccessRoute("viewer", "/upload")).toBe(false);
  });
});

describe("API error messages", () => {
  it("maps status codes to friendly text", () => {
    expect(friendlyApiError(401)).toMatch(/session|sign in/i);
    expect(friendlyApiError(403)).toMatch(/permission/i);
    expect(friendlyApiError(404)).toMatch(/not found/i);
    expect(friendlyApiError(422)).toMatch(/validation/i);
    expect(friendlyApiError(500)).toMatch(/server/i);
  });
});
