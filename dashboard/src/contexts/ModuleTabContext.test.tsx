import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ModuleTabProvider, useModuleTab } from "@/contexts/ModuleTabContext";

function TabReader() {
  return <span data-testid="tab">{useModuleTab()}</span>;
}

describe("ModuleTabContext", () => {
  it("provides tab value to descendants", () => {
    render(
      <ModuleTabProvider tab="pattern-agent">
        <TabReader />
      </ModuleTabProvider>
    );
    expect(screen.getByTestId("tab").textContent).toBe("pattern-agent");
  });

  it("falls back to overview outside provider", () => {
    render(<TabReader />);
    expect(screen.getByTestId("tab").textContent).toBe("overview");
  });
});
