"use client";

import { useCallback, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FolderOpen, UploadCloud } from "lucide-react";
import { uploadDatasetFolder, uploadFile } from "@/lib/api";
import { useUploadStore } from "@/store/upload-store";
import { useQueryClient } from "@tanstack/react-query";

function makeId() {
  return crypto.randomUUID();
}

export function UploadDropzone() {
  const [mode, setMode] = useState<"files" | "folder">("folder");
  const [busy, setBusy] = useState(false);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const upsert = useUploadStore((s) => s.upsertQueueItem);
  const update = useUploadStore((s) => s.updateQueueItem);
  const qc = useQueryClient();

  const processFiles = useCallback(
    async (accepted: File[], asFolder: boolean) => {
      if (!accepted.length) return;
      setBusy(true);
      try {
        if (asFolder) {
          const relativePaths = accepted.map(
            (f) => (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name,
          );
          const queueId = makeId();
          upsert({
            id: queueId,
            name: `Folder dataset (${accepted.length} files)`,
            size: accepted.reduce((a, f) => a + f.size, 0),
            status: "uploading",
            progress: 20,
          });
          try {
            const result = await uploadDatasetFolder(
              `dataset_${new Date().toISOString().slice(0, 19)}`,
              accepted,
              relativePaths,
              true,
            );
            update(queueId, {
              status: "completed",
              progress: 100,
              uploadId: result.dataset_id,
            });
          } catch (err) {
            update(queueId, {
              status: "failed",
              progress: 100,
              error: err instanceof Error ? err.message : "Folder upload failed",
            });
          }
        } else {
          for (const file of accepted) {
            const id = makeId();
            upsert({
              id,
              name: file.name,
              size: file.size,
              status: "uploading",
              progress: 15,
            });
            try {
              const result = await uploadFile(file, { asyncProcess: true });
              update(id, {
                status: "processing",
                progress: 60,
                uploadId: result.upload_id || result.upload?.id,
              });
            } catch (err) {
              update(id, {
                status: "failed",
                progress: 100,
                error: err instanceof Error ? err.message : "Upload failed",
              });
            }
          }
        }
        await qc.invalidateQueries({ queryKey: ["uploads"] });
        await qc.invalidateQueries({ queryKey: ["datasets"] });
        await qc.invalidateQueries({ queryKey: ["ingestion-stats"] });
      } finally {
        setBusy(false);
      }
    },
    [qc, update, upsert],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => processFiles(files, mode === "folder"),
    multiple: true,
    disabled: busy || mode === "folder",
    noClick: mode === "folder",
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setMode("folder")}
          className={`rounded-lg px-3 py-1.5 text-sm ${mode === "folder" ? "bg-[var(--accent)] text-white" : "bg-white/5 text-[var(--muted)]"}`}
        >
          Folder Upload
        </button>
        <button
          type="button"
          onClick={() => setMode("files")}
          className={`rounded-lg px-3 py-1.5 text-sm ${mode === "files" ? "bg-[var(--accent)] text-white" : "bg-white/5 text-[var(--muted)]"}`}
        >
          File Upload
        </button>
      </div>

      <div
        {...getRootProps()}
        onClick={
          mode === "folder"
            ? () => folderInputRef.current?.click()
            : getRootProps().onClick
        }
        className={`glass-panel cursor-pointer rounded-2xl border-dashed border-white/15 p-10 text-center transition ${
          isDragActive ? "accent-ring border-[var(--accent)]" : ""
        }`}
      >
        {mode === "files" ? (
          <input {...getInputProps()} data-testid="file-input" />
        ) : (
          <input
            ref={folderInputRef}
            type="file"
            className="hidden"
            multiple
            data-testid="folder-input"
            // @ts-expect-error non-standard directory selection attributes
            webkitdirectory=""
            directory=""
            onChange={(e) => {
              const files = Array.from(e.target.files || []);
              void processFiles(files, true);
              e.target.value = "";
            }}
          />
        )}
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--accent-soft)] text-[var(--accent)]">
          {mode === "folder" ? <FolderOpen /> : <UploadCloud />}
        </div>
        <div className="text-lg font-medium">
          {busy
            ? "Uploading…"
            : isDragActive
              ? "Drop files to ingest"
              : "Drag & drop STIL / LOG / CSV / JSON / XML"}
        </div>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Recursive folder support · checksum dedupe · PostgreSQL persistence · async queue
        </p>
      </div>
    </div>
  );
}
