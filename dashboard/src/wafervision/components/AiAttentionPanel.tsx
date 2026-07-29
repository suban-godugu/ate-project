"use client";

import { useCallback, useState } from "react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { WaferCanvasPanel } from "@/wafervision/components/WaferCanvasPanel";
import {
  drawFailureOverlay,
  drawOriginalWafer,
  type WaferRenderInput,
} from "@/wafervision/utils/waferRender";
import type {
  GradcamMeta,
  VisualizationData,
  VisualizationDensity,
  VisualizationGradcam,
} from "@/wafervision/types";
import {
  drawDensityData,
  drawGradcamData,
} from "@/wafervision/utils/visualizationDataRender";

type FallbackView = "placeholder" | "original" | "overlay" | "density";

const UNAVAILABLE_REASONS = [
  "CNN model not loaded",
  "Explainability disabled",
  "Prediction not supported",
  "Grad-CAM generation failed",
];

interface Props {
  /** Native backend CAM scalar grid (normally 7×7), never a PNG. */
  gradcam: VisualizationGradcam;
  /** Backend density points/KDE parameters for the quick-view action. */
  density: VisualizationDensity;
  coordinateSpace: VisualizationData["coordinate_space"];
  meta?: GradcamMeta;
  wafer: WaferRenderInput | null;
}

export function AiAttentionPanel({ gradcam, density, coordinateSpace, meta, wafer }: Props) {
  const { analyze, files, isAnalyzing } = useAnalysis();
  const [opacity, setOpacity] = useState(gradcam.alpha || 0.45);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [fallbackView, setFallbackView] = useState<FallbackView>("placeholder");

  const available = gradcam.available && Boolean(gradcam.heatmap) && meta?.available !== false;

  const drawAttention = useCallback(
    (ctx: CanvasRenderingContext2D, size: number) => {
      if (wafer) drawOriginalWafer(ctx, size, wafer);
      if (showHeatmap) drawGradcamData(ctx, size, gradcam, opacity);
    },
    [gradcam, opacity, showHeatmap, wafer],
  );

  const drawFallback = useCallback(
    (ctx: CanvasRenderingContext2D, size: number) => {
      if (fallbackView === "density") {
        drawDensityData(
          ctx,
          size,
          density,
          coordinateSpace.width,
          coordinateSpace.height,
        );
        return;
      }
      if (!wafer) return;
      if (fallbackView === "overlay") drawFailureOverlay(ctx, size, wafer);
      else drawOriginalWafer(ctx, size, wafer);
    },
    [coordinateSpace, density, fallbackView, wafer],
  );

  if (available) {
    const confidence =
      typeof meta?.confidence === "number" ? `${meta.confidence.toFixed(2)}%` : null;
    return (
      <WaferCanvasPanel
        label="Grad-CAM"
        draw={drawAttention}
        legend={
          <div className="space-y-1">
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-slate-400">
              {meta?.prediction_class ? <span>Prediction {meta.prediction_class}</span> : null}
              {confidence ? <span>Confidence {confidence}</span> : null}
              <span>{meta?.model || "ResNet50"}</span>
              <span>{meta?.layer || "layer4"}</span>
            </div>
            {meta?.wafer_trained === false ? (
              <p className="text-[10px] leading-snug text-amber-400/90">
                Uncalibrated — checkpoint head is not wafer-trained, so attention reflects
                backbone features, not learned defect classes.
              </p>
            ) : null}
          </div>
        }
        controls={
          <>
            <label className="ml-auto flex items-center gap-1 text-[10px] text-slate-400">
              <input
                type="checkbox"
                checked={showHeatmap}
                onChange={(e) => setShowHeatmap(e.target.checked)}
                className="accent-[#7C3AED]"
              />
              Heatmap
            </label>
            <label className="flex items-center gap-1.5 text-[10px] text-slate-400">
              Opacity {Math.round(opacity * 100)}%
              <input
                type="range"
                min={0.1}
                max={1}
                step={0.05}
                value={opacity}
                onChange={(e) => setOpacity(Number(e.target.value))}
                className="w-16 accent-[#7C3AED]"
              />
            </label>
          </>
        }
        footnote={`AI attention blended over the original wafer at ${Math.round(opacity * 100)}% opacity`}
      />
    );
  }

  if (fallbackView !== "placeholder") {
    const titles: Record<Exclude<FallbackView, "placeholder">, string> = {
      original: "Original Wafer",
      overlay: "Failure Overlay",
      density: "Failure Density Map",
    };
    return (
      <WaferCanvasPanel
        label={titles[fallbackView]}
        draw={drawFallback}
        controls={
          <button
            type="button"
            onClick={() => setFallbackView("placeholder")}
            className="ml-auto rounded border px-1.5 py-0.5 text-[10px] text-slate-300"
            style={{ borderColor: "var(--line)" }}
          >
            Back to Grad-CAM
          </button>
        }
        footnote="Substitute view — Grad-CAM is unavailable for this wafer"
      />
    );
  }

  return (
    <WaferCanvasPanel
      label="Grad-CAM"
      draw={null}
      emptyState={
        <div className="flex flex-col items-center gap-2 px-3 py-2 text-center">
          <span className="text-sm font-semibold text-slate-200">Grad-CAM Unavailable</span>
          <p className="max-w-[18rem] text-[11px] leading-relaxed text-slate-400">
            No trained wafer CNN model is available to generate AI attention visualization.
          </p>
          <div className="w-full max-w-[18rem] text-left">
            <p className="text-[10px] uppercase tracking-wide text-slate-500">Possible reasons</p>
            <ul className="mt-1 space-y-0.5">
              {UNAVAILABLE_REASONS.map((reason) => (
                <li key={reason} className="flex items-start gap-1.5 text-[11px] text-slate-500">
                  <span className="mt-[6px] h-1 w-1 shrink-0 rounded-full bg-slate-600" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-1 flex flex-wrap items-center justify-center gap-1.5">
            <button
              type="button"
              onClick={analyze}
              disabled={isAnalyzing || files.length === 0}
              className="rounded-lg bg-[#7C3AED] px-2.5 py-1 text-[11px] font-semibold text-white transition hover:bg-[#6D28D9] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isAnalyzing ? "Retrying…" : "Retry Generation"}
            </button>
            <button
              type="button"
              onClick={() => setFallbackView("original")}
              disabled={!wafer}
              className="rounded-lg border px-2.5 py-1 text-[11px] text-slate-300 disabled:opacity-40"
              style={{ borderColor: "var(--line)" }}
            >
              View Original Wafer
            </button>
            <button
              type="button"
              onClick={() => setFallbackView("overlay")}
              disabled={!wafer}
              className="rounded-lg border px-2.5 py-1 text-[11px] text-slate-300 disabled:opacity-40"
              style={{ borderColor: "var(--line)" }}
            >
              View Failure Overlay
            </button>
            <button
              type="button"
              onClick={() => setFallbackView("density")}
              disabled={!density.points.length}
              className="rounded-lg border px-2.5 py-1 text-[11px] text-slate-300 disabled:opacity-40"
              style={{ borderColor: "var(--line)" }}
            >
              View Density Map
            </button>
          </div>
        </div>
      }
      footnote={meta?.message || "Requires a wafer-trained CNN checkpoint"}
    />
  );
}
