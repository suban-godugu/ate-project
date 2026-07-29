"use client";

import { useCallback, useEffect, useRef } from "react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  WAFER_ANALYZE,
  WAFER_PICK_FILES,
  WAFER_PICK_FOLDER,
} from "@/wafervision/uploadBridge";

const IMAGE_ACCEPT = ".jpg,.jpeg,.png,.bmp,image/jpeg,image/png,image/bmp";

/**
 * Invisible host: header Upload Data / Upload Log File / Generate Yield Analysis
 * drive the same pickers + analyze as the removed Workspace Controls.
 */
export function WaferUploadHost() {
  const { setFiles, analyze, isAnalyzing, files } = useAnalysis();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = folderInputRef.current;
    if (!el) return;
    el.setAttribute("webkitdirectory", "");
    el.setAttribute("directory", "");
  }, []);

  const mergeFiles = useCallback(
    (incoming: FileList | File[]) => {
      const list = Array.from(incoming).filter((f) =>
        /\.(jpe?g|png|bmp)$/i.test(f.name)
      );
      if (!list.length) return;
      setFiles(list);
    },
    [setFiles]
  );

  useEffect(() => {
    const onPickFiles = () => {
      if (!isAnalyzing) fileInputRef.current?.click();
    };
    const onPickFolder = () => {
      if (!isAnalyzing) folderInputRef.current?.click();
    };
    const onAnalyze = () => {
      if (files.length > 0 && !isAnalyzing) analyze();
    };
    window.addEventListener(WAFER_PICK_FILES, onPickFiles);
    window.addEventListener(WAFER_PICK_FOLDER, onPickFolder);
    window.addEventListener(WAFER_ANALYZE, onAnalyze);
    return () => {
      window.removeEventListener(WAFER_PICK_FILES, onPickFiles);
      window.removeEventListener(WAFER_PICK_FOLDER, onPickFolder);
      window.removeEventListener(WAFER_ANALYZE, onAnalyze);
    };
  }, [analyze, files.length, isAnalyzing]);

  return (
    <div className="sr-only" aria-hidden>
      <input
        ref={fileInputRef}
        type="file"
        accept={IMAGE_ACCEPT}
        multiple
        disabled={isAnalyzing}
        onChange={(e) => e.target.files && mergeFiles(e.target.files)}
      />
      <input
        ref={folderInputRef}
        type="file"
        accept={IMAGE_ACCEPT}
        multiple
        disabled={isAnalyzing}
        onChange={(e) => e.target.files && mergeFiles(e.target.files)}
      />
    </div>
  );
}
