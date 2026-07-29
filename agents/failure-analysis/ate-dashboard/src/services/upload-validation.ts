export function validateUploadInputs(stilFile: File | null, logFiles: File[]) {
  if (!stilFile) {
    throw Object.assign(new Error("STIL file is required"), { code: "invalid_stil" });
  }
  if (!stilFile.name.toLowerCase().endsWith(".stil")) {
    throw Object.assign(new Error("Invalid STIL"), { code: "invalid_stil" });
  }
  if (!logFiles.length) {
    throw Object.assign(new Error("At least one tester log is required"), {
      code: "invalid_tester_logs",
    });
  }
  const validLog = logFiles.some((f) =>
    /\.(log|txt|stdf|std|dat|csv)$/i.test(f.name),
  );
  if (!validLog) {
    throw Object.assign(new Error("Invalid Tester Logs"), { code: "invalid_tester_logs" });
  }
}
