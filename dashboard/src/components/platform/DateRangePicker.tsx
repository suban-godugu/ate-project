"use client";

import { Calendar as CalendarIcon } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useQueryClient } from "@tanstack/react-query";
import { useFilterStore } from "@/stores/filterStore";
import type { DatePreset } from "@/types/platform";
import { getDateRangeLabel } from "@/lib/filterEngine";

const presets: { id: DatePreset; label: string }[] = [
  { id: "today", label: "Today" },
  { id: "yesterday", label: "Yesterday" },
  { id: "7d", label: "Last 7 Days" },
  { id: "30d", label: "Last 30 Days" },
  { id: "this-month", label: "This Month" },
  { id: "custom", label: "Custom Range" },
];

export function DateRangePicker() {
  const filters = useFilterStore((s) => s.filters);
  const setFilters = useFilterStore((s) => s.setFilters);
  const queryClient = useQueryClient();

  const applyPreset = (datePreset: DatePreset) => {
    setFilters({ datePreset });
    queryClient.invalidateQueries();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 hover:bg-white/5 hover:text-white sm:h-10 sm:w-10"
        aria-label={`Date range: ${getDateRangeLabel(filters)}`}
      >
        <CalendarIcon className="h-4 w-4" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64 border-[#2D3748] bg-[#111827]">
        <DropdownMenuGroup>
          <DropdownMenuLabel className="text-slate-400">Date Range</DropdownMenuLabel>
          {presets.map((preset) => (
            <DropdownMenuItem
              key={preset.id}
              onClick={() => applyPreset(preset.id)}
              className={filters.datePreset === preset.id ? "bg-[#7C3AED]/20 text-white" : ""}
            >
              {preset.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
        {filters.datePreset === "custom" && (
          <>
            <DropdownMenuSeparator className="bg-[#2D3748]" />
            <div className="space-y-2 p-2">
              <Input
                type="date"
                value={filters.customDateFrom}
                onChange={(e) => {
                  setFilters({ customDateFrom: e.target.value });
                  queryClient.invalidateQueries();
                }}
                className="h-8 border-[#2D3748] bg-[#0A1020] text-xs"
                aria-label="Custom start date"
                suppressHydrationWarning
              />
              <Input
                type="date"
                value={filters.customDateTo}
                onChange={(e) => {
                  setFilters({ customDateTo: e.target.value });
                  queryClient.invalidateQueries();
                }}
                className="h-8 border-[#2D3748] bg-[#0A1020] text-xs"
                aria-label="Custom end date"
                suppressHydrationWarning
              />
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
