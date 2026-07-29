import { describe, expect, it } from "vitest";
import { useToastStore, notify } from "@/stores/toastStore";

describe("toastStore", () => {
  it("pushes and dismisses toasts", () => {
    useToastStore.setState({ toasts: [] });
    notify({ title: "Upload Complete", variant: "success" });
    expect(useToastStore.getState().toasts).toHaveLength(1);
    const id = useToastStore.getState().toasts[0].id;
    useToastStore.getState().dismiss(id);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("caps toast queue at five items", () => {
    useToastStore.setState({ toasts: [] });
    for (let i = 0; i < 7; i++) {
      notify({ title: `Toast ${i}`, variant: "info" });
    }
    expect(useToastStore.getState().toasts.length).toBeLessThanOrEqual(5);
  });
});
