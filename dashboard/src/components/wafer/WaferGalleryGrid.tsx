"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useWaferNavigation } from "@/components/wafer/WaferNavigationContext";
import type { WaferGalleryCard } from "@/types/wafer";

function WaferImage({
  src,
  alt,
  height = 180,
}: {
  src: string;
  alt: string;
  height?: number;
}) {
  return (
    <div className="flex items-center justify-center" style={{ height }}>
      <img
        src={src}
        alt={alt}
        className="max-h-full max-w-full rounded-full object-contain"
        style={{ imageRendering: "pixelated" }}
      />
    </div>
  );
}

export function WaferGalleryGrid({ cards }: { cards: WaferGalleryCard[] }) {
  const navigate = useWaferNavigation();

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((card, i) => (
        <motion.button
          key={card.id}
          type="button"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.05 }}
          onClick={() => navigate(card.id)}
          className="glass-card gradient-border hover-lift group overflow-hidden text-left"
        >
          <div className="relative border-b border-[#2D3748]/60 bg-[#0A1020]/60 p-4">
            <WaferImage src={card.images.wafer} alt={`${card.label} wafer`} height={160} />
            <div className="absolute right-3 top-3 flex flex-col gap-1">
              <img
                src={card.images.overlay}
                alt={`${card.label} overlay`}
                className="h-12 w-12 rounded-full border border-[#7C3AED]/40 object-cover"
                style={{ imageRendering: "pixelated" }}
              />
              <img
                src={card.images.density}
                alt={`${card.label} density`}
                className="h-12 w-12 rounded-full border border-[#2D3748] object-cover"
                style={{ imageRendering: "pixelated" }}
              />
            </div>
            <div className="absolute left-3 top-3 rounded-lg bg-[#111827]/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[#A78BFA]">
              {card.label}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 p-4">
            <div>
              <p className="text-[10px] uppercase text-slate-500">Avg Yield</p>
              <p className="text-lg font-bold text-white">{card.avgYield}%</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-slate-500">Confidence</p>
              <p className="text-lg font-bold text-[#A78BFA]">{card.confidence}%</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-slate-500">Good Dies</p>
              <p className="text-sm font-semibold text-emerald-400">{card.goodDies.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-slate-500">Bad Dies</p>
              <p className="text-sm font-semibold text-red-400">{card.badDies.toLocaleString()}</p>
            </div>
          </div>
          <div className="flex items-center justify-between border-t border-[#2D3748]/40 px-4 py-3 text-xs text-slate-400">
            <span>{card.totalDies.toLocaleString()} total dies</span>
            <span className="flex items-center gap-1 text-[#7C3AED] group-hover:underline">
              View analysis
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
        </motion.button>
      ))}
    </div>
  );
}
