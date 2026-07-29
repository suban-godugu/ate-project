/** Bridge header Upload buttons ↔ WaferVision Workspace Controls */

export const WAFER_PICK_FILES = "wafervision:pick-files";
export const WAFER_PICK_FOLDER = "wafervision:pick-folder";
export const WAFER_ANALYZE = "wafervision:analyze";

export function requestWaferFileUpload() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(WAFER_PICK_FILES));
}

export function requestWaferFolderUpload() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(WAFER_PICK_FOLDER));
}

export function requestWaferAnalyze() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(WAFER_ANALYZE));
}
