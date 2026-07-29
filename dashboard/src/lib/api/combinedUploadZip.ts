import JSZip from "jszip";

/** Bundle one STIL/data file + one or more ATE logs into a ZIP for a single pipeline job. */
export async function buildCombinedUploadZip(
  stilFile: File,
  logFiles: File[],
  zipName = "verilumen_combined_upload.zip"
): Promise<File> {
  if (!stilFile) throw new Error("STIL / data file is required");
  if (!logFiles.length) throw new Error("At least one ATE log file is required");

  const zip = new JSZip();
  zip.file(stilFile.name, stilFile);
  const used = new Set<string>([stilFile.name.toLowerCase()]);

  for (const log of logFiles) {
    let name = log.name;
    const key = name.toLowerCase();
    if (used.has(key)) {
      const dot = name.lastIndexOf(".");
      const base = dot > 0 ? name.slice(0, dot) : name;
      const ext = dot > 0 ? name.slice(dot) : "";
      let i = 2;
      while (used.has(`${base}_${i}${ext}`.toLowerCase())) i += 1;
      name = `${base}_${i}${ext}`;
    }
    used.add(name.toLowerCase());
    zip.file(name, log);
  }

  const blob = await zip.generateAsync({ type: "blob", compression: "DEFLATE" });
  return new File([blob], zipName, { type: "application/zip" });
}
