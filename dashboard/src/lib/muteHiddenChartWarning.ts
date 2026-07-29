const HIDDEN_CHART_WARNING = "of chart should be greater than 0";

/**
 * Charts kept mounted inside hidden containers (see TabPanelHost, which keeps
 * visited tabs behind `display: none`) measure 0x0, and Recharts warns on every
 * render. They size correctly as soon as their container is shown, so drop only
 * that message and leave every other warning intact.
 */
export function muteHiddenChartWarning(): void {
  if (typeof window === "undefined") return;
  const flagged = window as typeof window & { __hiddenChartWarningMuted?: boolean };
  if (flagged.__hiddenChartWarningMuted) return;
  flagged.__hiddenChartWarningMuted = true;

  const originalWarn = console.warn.bind(console);
  console.warn = (...args: unknown[]) => {
    if (typeof args[0] === "string" && args[0].includes(HIDDEN_CHART_WARNING)) return;
    originalWarn(...args);
  };
}
