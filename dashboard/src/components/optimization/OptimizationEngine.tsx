"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import type { OptimizationParams } from "@/types/dashboard";

interface OptimizationEngineProps {
  onRun: (params: OptimizationParams) => void;
  isRunning?: boolean;
}

export function OptimizationEngine({ onRun, isRunning }: OptimizationEngineProps) {
  const [params, setParams] = useState<OptimizationParams>({
    maxCost: 2500,
    yieldTarget: 95,
    maxTestTime: 45,
  });

  const update = (key: keyof OptimizationParams, value: number) => {
    setParams((p) => ({ ...p, [key]: value }));
  };

  return (
    <div id="optimization" className="glass-card gradient-border p-6">
      <div className="mb-6">
        <h3 className="text-base font-semibold text-white">Test Optimization Engine</h3>
        <p className="text-sm text-slate-400">
          Configure constraints and run AI-assisted test program optimization
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <div className="mb-2 flex justify-between text-sm">
            <span className="text-slate-400">Maximum Cost</span>
            <span className="font-medium text-white">${params.maxCost.toLocaleString()}</span>
          </div>
          <Slider
            value={[params.maxCost]}
            onValueChange={(v) => {
              const val = Array.isArray(v) ? v[0] : v;
              update("maxCost", val ?? params.maxCost);
            }}
            min={1000}
            max={5000}
            step={100}
          />
        </div>

        <div>
          <div className="mb-2 flex justify-between text-sm">
            <span className="text-slate-400">Yield Target</span>
            <span className="font-medium text-white">{params.yieldTarget}%</span>
          </div>
          <Slider
            value={[params.yieldTarget]}
            onValueChange={(v) => {
              const val = Array.isArray(v) ? v[0] : v;
              update("yieldTarget", val ?? params.yieldTarget);
            }}
            min={85}
            max={99}
            step={0.5}
          />
        </div>

        <div>
          <div className="mb-2 flex justify-between text-sm">
            <span className="text-slate-400">Maximum Test Time</span>
            <span className="font-medium text-white">{params.maxTestTime}s</span>
          </div>
          <Slider
            value={[params.maxTestTime]}
            onValueChange={(v) => {
              const val = Array.isArray(v) ? v[0] : v;
              update("maxTestTime", val ?? params.maxTestTime);
            }}
            min={20}
            max={120}
            step={1}
          />
        </div>
      </div>

      <motion.div
        className="mt-8"
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        <Button
          className="btn-glow h-12 w-full rounded-xl bg-[#7C3AED] text-base font-semibold hover:bg-[#6D28D9]"
          disabled={isRunning}
          onClick={() => onRun(params)}
        >
          <motion.span
            animate={isRunning ? { rotate: 360 } : {}}
            transition={{ repeat: isRunning ? Infinity : 0, duration: 1, ease: "linear" }}
            className="mr-2 inline-flex"
          >
            <Sparkles className="h-5 w-5" />
          </motion.span>
          {isRunning ? "Running AI Optimization..." : "Run AI Optimization"}
        </Button>
      </motion.div>
    </div>
  );
}
