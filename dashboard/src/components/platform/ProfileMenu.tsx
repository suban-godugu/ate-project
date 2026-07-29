"use client";

import { useRouter } from "next/navigation";
import { LogOut, Settings, User } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
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
import { useUserStore } from "@/stores/userStore";
import { defaultAccountPreset } from "@/types/theme";

export function ProfileMenu({ compact = false }: { compact?: boolean }) {
  const storedProfile = useUserStore((s) => s.profile);
  const hydrated = useHydrated();
  const profile = hydrated ? storedProfile : { ...defaultAccountPreset, avatarInitials: "AJ", password: "" };
  const router = useRouter();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="hidden items-center gap-2 rounded-xl border border-[#2D3748]/60 bg-[#111827]/50 px-2 py-1.5 lg:inline-flex lg:gap-2.5 lg:px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]/50"
        aria-label="Open profile menu"
        suppressHydrationWarning
      >
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-[#7C3AED] text-xs text-white">
            {profile.avatarInitials}
          </AvatarFallback>
        </Avatar>
        {!compact && (
          <div className="hidden text-left xl:block">
            <p className="text-sm font-medium text-white">{profile.name}</p>
            <p className="text-[11px] text-slate-400">{profile.role}</p>
          </div>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 border-[#2D3748] bg-[#111827]">
        <DropdownMenuGroup>
          <DropdownMenuLabel>
            <div>
              <p className="text-sm text-white">{profile.name}</p>
              <p className="text-xs font-normal text-slate-400">{profile.email}</p>
            </div>
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator className="bg-[#2D3748]" />
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => router.push("/dashboard/settings")}>
            <User className="mr-2 h-4 w-4" /> Profile & Account
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push("/dashboard/settings")}>
            <Settings className="mr-2 h-4 w-4" /> Settings
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator className="bg-[#2D3748]" />
        <DropdownMenuGroup>
          <DropdownMenuItem disabled className="text-slate-500">
            <LogOut className="mr-2 h-4 w-4" /> Sign out (demo)
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ProfileBadgeMobile() {
  const storedProfile = useUserStore((s) => s.profile);
  const hydrated = useHydrated();
  const initials = hydrated ? storedProfile.avatarInitials : "AJ";

  return (
    <div className="inline-flex h-9 w-9 items-center justify-center rounded-xl lg:hidden" aria-label="Profile">
      <Avatar className="h-7 w-7">
        <AvatarFallback className="bg-[#7C3AED] text-[10px] text-white">{initials}</AvatarFallback>
      </Avatar>
    </div>
  );
}
