"use client";

import { memo, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { searchPlatform } from "@/lib/searchIndex";
import { useFilterStore } from "@/stores/filterStore";
import { cn } from "@/lib/utils";

interface GlobalSearchProps {
  placeholder?: string;
  className?: string;
  compact?: boolean;
}

export const GlobalSearch = memo(function GlobalSearch({
  placeholder = "Search patterns, lots, wafers, equipment...",
  className,
  compact = false,
}: GlobalSearchProps) {
  const { searchQuery, setSearchQuery } = useFilterStore();
  const [open, setOpen] = useState(false);
  const [localQuery, setLocalQuery] = useState(searchQuery);
  const containerRef = useRef<HTMLDivElement>(null);

  const results = useMemo(() => searchPlatform(localQuery), [localQuery]);

  useEffect(() => {
    const timer = setTimeout(() => setSearchQuery(localQuery), 200);
    return () => clearTimeout(timer);
  }, [localQuery, setSearchQuery]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" aria-hidden="true" />
      <Input
        value={localQuery}
        onChange={(e) => {
          setLocalQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={placeholder}
        aria-label="Global search"
        role="combobox"
        aria-expanded={open && results.length > 0}
        aria-controls="global-search-results"
        className={cn(
          "h-11 rounded-xl border-[#2D3748] bg-[#111827]/80 pl-11 text-sm backdrop-blur-sm focus-visible:border-[#7C3AED] focus-visible:ring-[#7C3AED]/30",
          compact && "h-9 text-xs"
        )}
      />
      {open && localQuery.trim() && (
        <div
          id="global-search-results"
          role="listbox"
          className="absolute left-0 right-0 top-[calc(100%+8px)] z-50 max-h-80 overflow-y-auto rounded-xl border border-[#2D3748] bg-[#111827] p-2 shadow-2xl"
        >
          {results.length === 0 ? (
            <p className="px-3 py-4 text-sm text-slate-400">No results for &quot;{localQuery}&quot;</p>
          ) : (
            results.map((item) => (
              <Link
                key={`${item.category}-${item.id}`}
                href={item.route}
                role="option"
                onClick={() => {
                  setOpen(false);
                  setLocalQuery("");
                }}
                className="block rounded-lg px-3 py-2.5 transition-colors hover:bg-[#7C3AED]/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]/50"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-white">{item.title}</p>
                  <span className="text-[10px] text-[#7C3AED]">{item.category}</span>
                </div>
                <p className="text-xs text-slate-400">{item.subtitle}</p>
                <p className="text-[10px] text-slate-500">Matched: {item.matchedField}</p>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  );
});
