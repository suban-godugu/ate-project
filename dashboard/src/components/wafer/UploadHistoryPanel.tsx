"use client";

import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { WaferUploadHistoryItem } from "@/types/wafer";
import { cn } from "@/lib/utils";

export function UploadHistoryPanel({
  items,
  selectedId,
  onSelect,
  title = "Upload History",
}: {
  items: WaferUploadHistoryItem[];
  selectedId: string;
  onSelect: (item: WaferUploadHistoryItem) => void;
  title?: string;
}) {
  return (
    <div className="glass-card gradient-border p-5">
      <h3 className="mb-1 text-base font-semibold text-white">{title}</h3>
      <p className="mb-4 text-sm text-slate-400">
        All uploaded wafers — select a row to view overlay and fail density maps
      </p>
      <div className="overflow-hidden rounded-xl border border-[#2D3748]/60">
        <div className="grid grid-cols-[48px_1fr_1fr_1fr_90px_72px] gap-2 border-b border-[#2D3748]/60 bg-[#0A1020]/80 px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          <span />
          <span>Wafer</span>
          <span>Lot</span>
          <span>Upload Date</span>
          <span>Confidence</span>
          <span className="text-right">Action</span>
        </div>
        <ul className="max-h-[320px] divide-y divide-[#2D3748]/40 overflow-y-auto">
          {items.map((item) => {
            const selected = item.id === selectedId;
            return (
              <li
                key={item.id}
                className={cn(
                  "grid grid-cols-[48px_1fr_1fr_1fr_90px_72px] items-center gap-2 px-4 py-3 text-sm transition-colors",
                  selected
                    ? "bg-[#7C3AED]/15 ring-1 ring-inset ring-[#7C3AED]/50"
                    : "hover:bg-[#111827]/80"
                )}
              >
                <button
                  type="button"
                  onClick={() => onSelect(item)}
                  className="col-span-5 grid grid-cols-[48px_1fr_1fr_1fr_90px] items-center gap-2 text-left"
                >
                  <img
                    src={item.images.wafer}
                    alt={item.wafer}
                    className="h-10 w-10 rounded-full border border-[#2D3748] object-cover"
                    style={{ imageRendering: "pixelated" }}
                  />
                  <span className="font-mono font-medium text-white">{item.wafer}</span>
                  <span className="truncate text-slate-400">{item.lot}</span>
                  <span className="truncate text-xs text-slate-500">{item.uploadDate}</span>
                  <span className="font-semibold text-[#A78BFA]">{item.confidence}%</span>
                </button>
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs text-red-400 hover:text-red-300"
                    aria-label={`Delete ${item.wafer}`}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
