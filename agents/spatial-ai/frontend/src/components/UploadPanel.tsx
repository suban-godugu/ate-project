"use client";

import { FolderOpen, UploadCloud } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import { ACCEPTED_EXTENSIONS, cn } from "@/utils/format";

function isAccepted(file: File): boolean {
  const lower = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export function UploadPanel() {
  const { files, setFiles, isAnalyzing } = useAnalysis();
  const inputRef = useRef<HTMLInputElement>(null);
  const folderRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const applyFiles = useCallback(
    (list: FileList | File[], append = false) => {
      const next = Array.from(list).filter(isAccepted);
      setFiles(append ? [...files, ...next] : next);
    },
    [files, setFiles],
  );

  return (
    <section className="panel p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="panel-title">Upload Panel</h2>
        <span className="text-xs text-[var(--muted)]">jpg · jpeg · png · bmp</span>
      </div>

      <div
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-8 transition",
          dragging
            ? "border-signal-info bg-signal-info/5"
            : "border-[var(--line)] hover:border-ink-400",
          isAnalyzing && "pointer-events-none opacity-60",
        )}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          if (event.dataTransfer.files?.length) applyFiles(event.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
      >
        <UploadCloud className="mb-3 h-8 w-8 text-ink-500" />
        <p className="text-sm font-medium">Drag & drop wafer images</p>
        <p className="mt-1 text-xs text-[var(--muted)]">
          1 or N wafers · click to browse
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.bmp,image/jpeg,image/png,image/bmp"
          multiple
          className="hidden"
          onChange={(event) => {
            if (event.target.files) applyFiles(event.target.files);
          }}
        />
      </div>

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          disabled={isAnalyzing}
          onClick={() => folderRef.current?.click()}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium disabled:opacity-50"
        >
          <FolderOpen className="h-3.5 w-3.5" />
          Folder Upload
        </button>
        <input
          ref={(el) => {
            folderRef.current = el;
            if (el) {
              el.setAttribute("webkitdirectory", "");
              el.setAttribute("directory", "");
            }
          }}
          type="file"
          multiple
          className="hidden"
          onChange={(event) => {
            if (event.target.files) applyFiles(event.target.files);
          }}
        />      </div>

      {files.length > 0 && (
        <ul className="mt-4 max-h-28 space-y-1 overflow-auto text-xs text-[var(--muted)]">
          {files.map((file) => (
            <li key={`${file.name}-${file.size}-${file.lastModified}`} className="truncate font-mono">
              {file.webkitRelativePath || file.name}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
