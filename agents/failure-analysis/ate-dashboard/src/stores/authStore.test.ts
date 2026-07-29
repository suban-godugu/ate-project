import { describe, expect, it, beforeEach } from "vitest";
import { useAuthStore } from "@/stores/authStore";

describe("authStore", () => {
  beforeEach(() => {
    useAuthStore.setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      hydrated: true,
    });
  });

  it("stores and clears session", () => {
    useAuthStore.getState().setSession({
      accessToken: "a",
      refreshToken: "r",
      user: {
        id: "1",
        email: "a@b.c",
        full_name: "Admin",
        role: "administrator",
        status: "active",
      },
    });
    expect(useAuthStore.getState().accessToken).toBe("a");
    useAuthStore.getState().clearSession();
    expect(useAuthStore.getState().user).toBeNull();
  });
});
