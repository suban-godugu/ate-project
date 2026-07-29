"use client";

import Link from "next/link";
import { Bell, CheckCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useHydrated } from "@/hooks/useHydrated";
import { useNotifications } from "@/hooks/useNotifications";
import type { NotificationSeverity } from "@/types/platform";
import { cn } from "@/lib/utils";

const sections: { key: NotificationSeverity; label: string }[] = [
  { key: "critical", label: "Critical Alerts" },
  { key: "warning", label: "Warnings" },
  { key: "info", label: "Information" },
  { key: "system", label: "System Messages" },
];

function severityColor(severity: NotificationSeverity) {
  switch (severity) {
    case "critical":
      return "bg-red-500/20 text-red-400";
    case "warning":
      return "bg-orange-500/20 text-orange-400";
    case "info":
      return "bg-blue-500/20 text-blue-400";
    default:
      return "bg-slate-500/20 text-slate-400";
  }
}

export function NotificationCenter() {
  const { notifications, markRead, markAllRead } = useNotifications();
  const hydrated = useHydrated();
  const unreadCount = hydrated ? notifications.filter((n) => !n.read).length : 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="relative inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 hover:bg-white/5 hover:text-white sm:h-10 sm:w-10"
        aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}
        suppressHydrationWarning
      >
        <Bell className="h-4 w-4" />
        {hydrated && unreadCount > 0 && (
          <Badge className="absolute -right-0.5 -top-0.5 h-4 min-w-4 rounded-full bg-red-500 px-1 text-[10px] text-white">
            {unreadCount}
          </Badge>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 border-[#2D3748] bg-[#111827]">
        <DropdownMenuGroup>
          <div className="flex items-center justify-between px-2 py-1.5">
            <DropdownMenuLabel className="p-0 text-slate-300">Notifications</DropdownMenuLabel>
            <Button variant="ghost" size="sm" className="h-7 text-[11px] text-[#7C3AED]" onClick={markAllRead}>
              <CheckCheck className="mr-1 h-3 w-3" />
              Mark All Read
            </Button>
          </div>
        </DropdownMenuGroup>
        <DropdownMenuSeparator className="bg-[#2D3748]" />
        {sections.map((section) => {
          const items = notifications.filter((n) => n.severity === section.key);
          if (!items.length) return null;
          return (
            <DropdownMenuGroup key={section.key}>
              <DropdownMenuLabel className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                {section.label}
              </DropdownMenuLabel>
              {items.map((item) => (
                <DropdownMenuItem
                  key={item.id}
                  className={cn("flex flex-col items-start gap-1 py-2", !item.read && "bg-white/5")}
                  onClick={() => markRead(item.id)}
                >
                  <div className="flex w-full items-center justify-between gap-2">
                    <span className="text-sm font-medium text-white">{item.title}</span>
                    <span className={cn("rounded px-1.5 py-0.5 text-[10px]", severityColor(item.severity))}>
                      {item.severity}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400">{item.message}</span>
                  <div className="flex w-full items-center justify-between">
                    <span className="text-[10px] text-slate-500">{item.timestamp}</span>
                    {item.alertRoute && (
                      <Link href={item.alertRoute} className="text-[10px] text-[#7C3AED] hover:underline">
                        Open Alert
                      </Link>
                    )}
                  </div>
                </DropdownMenuItem>
              ))}
            </DropdownMenuGroup>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
