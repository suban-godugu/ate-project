import { describe, expect, it } from "vitest";
import { defaultThemeConfig } from "@/types/theme";

function mergeTheme(remote: Record<string, unknown>) {
  const merged: Record<string, unknown> = {};
  for (const key of Object.keys(defaultThemeConfig)) {
    const value = remote[key];
    if (value !== undefined && value !== null) merged[key] = value;
  }
  return merged;
}

describe("theme preferences merge", () => {
  it("merges remote theme_json over defaults", () => {
    const result = mergeTheme({
      primaryColor: "emerald",
      compactMode: true,
      animations: false,
    });
    expect(result.primaryColor).toBe("emerald");
    expect(result.compactMode).toBe(true);
    expect(result.appearance).toBeUndefined();
  });

  it("ignores unknown keys", () => {
    const result = mergeTheme({ primaryColor: "blue", unknownKey: "x" });
    expect(result.primaryColor).toBe("blue");
    expect(result).not.toHaveProperty("unknownKey");
  });
});
