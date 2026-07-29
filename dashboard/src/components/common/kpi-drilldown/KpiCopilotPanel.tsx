"use client";

import { useState } from "react";
import { Send, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface KpiCopilotPanelProps {
  open: boolean;
  onClose: () => void;
  kpiName: string;
  kpiValue: string;
  suggestedPrompts?: string[];
}

export function KpiCopilotPanel({ open, onClose, kpiName, kpiValue, suggestedPrompts }: KpiCopilotPanelProps) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "ai"; text: string }[]>([]);

  const prompts = suggestedPrompts?.length ? suggestedPrompts : [
    "Why did coverage drop?",
    "Why did the parser fail?",
    "Compare previous lot",
    "Show similar failures",
    "Predict next failure",
    "Recommend optimization",
  ];

  if (!open) return null;

  const ask = (text: string) => {
    if (!text.trim()) return;
    setMessages((m) => [
      ...m,
      { role: "user", text },
      {
        role: "ai",
        text: `${kpiName} (${kpiValue}): Signal points to timing marginality on SC-004821 during at-speed patterns. Similar failures detected on LOT-4418. Recommended: re-run ATPG on M3-IO, regenerate STIL for PAT-8821, schedule T-104 calibration. Predicted yield recovery +0.9–1.3%.`,
      },
    ]);
    setQuery("");
  };

  return (
    <div className="fixed bottom-20 right-6 z-[110] flex w-[400px] flex-col overflow-hidden rounded-2xl border border-[rgba(139,92,246,0.35)] bg-[#0B0F1A]/98 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-[#2D3748]/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[#8B5CF6]" />
          <span className="text-sm font-semibold text-white">AI Copilot</span>
        </div>
        <Button type="button" variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close copilot">
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="max-h-72 flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="space-y-2">
            {prompts.map((s) => (
              <button
                key={s}
                type="button"
                suppressHydrationWarning
                onClick={() => ask(s)}
                className="block w-full rounded-lg border border-[#2D3748]/60 px-3 py-2 text-left text-xs text-[#CBD5E1] transition hover:border-[rgba(139,92,246,0.4)]"
              >
                {s}
              </button>
            ))}
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "rounded-lg px-3 py-2 text-xs leading-relaxed",
                msg.role === "user" ? "ml-6 bg-[#8B5CF6]/20 text-white" : "mr-6 bg-[#1e293b]/80 text-[#CBD5E1]"
              )}
            >
              {msg.text}
            </div>
          ))
        )}
      </div>
      <div className="flex gap-2 border-t border-[#2D3748]/60 p-3">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask(query)}
          placeholder="Ask engineering question..."
          className="h-8 border-[#2D3748] bg-[#0A1020] text-xs"
          aria-label="AI copilot question"
        />
        <Button type="button" size="icon-sm" className="bg-[#8B5CF6] hover:bg-[#7C3AED]" onClick={() => ask(query)} aria-label="Send">
          <Send className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
