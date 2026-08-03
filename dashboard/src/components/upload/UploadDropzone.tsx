"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion } from "framer-motion";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadDropzoneProps {
  accept: Record<string, string[]>;
  maxSizeBytes: number;
  multiple?: boolean;
  onFilesSelected: (files: File[]) => void;
  label?: string;
  hint?: string;
}

export function UploadDropzone({
  accept,
  maxSizeBytes,
  multiple = false,
  onFilesSelected,
  label = "Drag & Drop files here",
  hint = "Click to Browse",
}: UploadDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length) onFilesSelected(accepted);
    },
    [onFilesSelected]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept,
    maxSize: maxSizeBytes,
    multiple,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-200",
        isDragActive && !isDragReject && "border-[#7C3AED] bg-[#7C3AED]/10",
        isDragReject && "border-red-500/50 bg-red-500/5",
        !isDragActive && "border-[#2D3748] bg-[#0A1020]/40 hover:border-[#7C3AED]/50 hover:bg-[#7C3AED]/5"
      )}
    >
      <input {...getInputProps()} />
      <motion.div animate={{ y: isDragActive ? -4 : 0 }} className="flex flex-col items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#7C3AED]/15 text-[#7C3AED]">
          <UploadCloud className="h-7 w-7" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">{label}</p>
          <p className="mt-1 text-xs text-slate-400">or {hint}</p>
        </div>
      </motion.div>
    </div>
  );
}
