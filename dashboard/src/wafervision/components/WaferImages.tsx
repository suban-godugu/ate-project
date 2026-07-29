"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { useWaferBaseImage } from "@/wafervision/hooks/useWaferBaseImage";
import { WaferCanvasPanel } from "@/wafervision/components/WaferCanvasPanel";
import { AiAttentionPanel } from "@/wafervision/components/AiAttentionPanel";
import {
  BinMapLegend,
  DensityLegend,
  OverlayLegend,
} from "@/wafervision/components/WaferLegends";
import {
  drawFailureOverlay,
  drawOriginalWafer,
  pickDie,
  type WaferRenderInput,
} from "@/wafervision/utils/waferRender";
import { drawDensityData } from "@/wafervision/utils/visualizationDataRender";

const RENDER_SIZE = 2048;

export function WaferImages() {
  const { selected } = useAnalysis();
  const [selectedDieId, setSelectedDieId] = useState<string | number | null>(null);
  const [showFailureLayer, setShowFailureLayer] = useState(true);
  const [showDensityLayer, setShowDensityLayer] = useState(true);
  const [showClusters, setShowClusters] = useState(true);
  const [markerAlpha, setMarkerAlpha] = useState(1);
  const [densityIntensity, setDensityIntensity] = useState(1);

  const dies = useMemo(() => selected?.dies ?? [], [selected]);
  // Only the most severe clusters get outlines; all 20 would clutter the map.
  const clusters = useMemo(
    () => (selected?.spatial_analysis?.clusters ?? []).slice(0, 6),
    [selected],
  );
  const visualization = selected?.visualization;

  useEffect(() => {
    setSelectedDieId(null);
    setMarkerAlpha(1);
    setDensityIntensity(1);
  }, [selected?.wafer_id]);

  const baseImage = useWaferBaseImage(selected?.images?.original);

  const wafer: WaferRenderInput | null = useMemo(
    () =>
      dies.length
        ? {
            dies,
            geometry: selected?.wafer_geometry,
            gridInfo: selected?.grid_info,
            image: baseImage,
          }
        : null,
    [baseImage, dies, selected?.grid_info, selected?.wafer_geometry],
  );

  const drawOriginal = useCallback(
    (ctx: CanvasRenderingContext2D, size: number) => {
      if (wafer) drawOriginalWafer(ctx, size, wafer);
    },
    [wafer],
  );

  const drawOverlay = useCallback(
    (ctx: CanvasRenderingContext2D, size: number) => {
      if (!wafer) return;
      if (!showFailureLayer) {
        drawOriginalWafer(ctx, size, wafer);
        return;
      }
      drawFailureOverlay(ctx, size, {
        ...wafer,
        selectedDieId,
        clusters,
        showClusters,
        markerAlpha,
      });
    },
    [clusters, markerAlpha, selectedDieId, showClusters, showFailureLayer, wafer],
  );

  const drawDensity = useCallback(
    (ctx: CanvasRenderingContext2D, size: number) => {
      const density = visualization?.density;
      const coordinateSpace = visualization?.coordinate_space;
      if (!density || !coordinateSpace) return;
      if (!showDensityLayer) {
        ctx.fillStyle = "#080d17";
        ctx.fillRect(0, 0, size, size);
        return;
      }
      drawDensityData(
        ctx,
        size,
        density,
        coordinateSpace.width,
        coordinateSpace.height,
        densityIntensity,
      );
    },
    [densityIntensity, showDensityLayer, visualization],
  );

  const onPickDie = useCallback(
    (x: number, y: number) => {
      const die = pickDie(dies, x, y);
      const id = die?.die_id ?? die?.id ?? null;
      setSelectedDieId((prev) => (prev != null && id != null && String(prev) === String(id) ? null : id));
    },
    [dies],
  );

  const selectedDie = useMemo(
    () =>
      selectedDieId == null
        ? null
        : dies.find((d) => String(d.die_id ?? d.id) === String(selectedDieId)) ?? null,
    [dies, selectedDieId],
  );

  if (!wafer || !visualization) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-3">Wafer Images</h2>
        <div className="flex aspect-[4/1] items-center justify-center rounded-lg border text-sm text-slate-500" style={{ borderColor: "var(--line)" }}>
          Visualization data unavailable. Re-run wafer analysis with the current Spatial API.
        </div>
      </section>
    );
  }

  return (
    <section className="panel p-5">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="panel-title">Wafer Images</h2>
          <p className="mt-1 text-[11px] text-slate-500">
            {baseImage ? "Original wafer image" : "Die bin map"} with visualization JSON layered at
            device resolution over {dies.length.toLocaleString()} dies.
          </p>
        </div>
        <fieldset className="flex flex-wrap items-center gap-3 rounded-lg border px-2.5 py-1.5 text-[11px] text-slate-400" style={{ borderColor: "var(--line)" }}>
          <legend className="px-1 text-[10px] uppercase tracking-wide text-slate-500">Layers</legend>
          <label className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={showFailureLayer}
              onChange={(e) => setShowFailureLayer(e.target.checked)}
              className="accent-[#EF4444]"
            />
            Overlay
          </label>
          <label className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={showDensityLayer}
              onChange={(e) => setShowDensityLayer(e.target.checked)}
              className="accent-[#F97316]"
            />
            Density
          </label>
          <label className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={showClusters}
              onChange={(e) => setShowClusters(e.target.checked)}
              className="accent-[#FB923C]"
            />
            Clusters
          </label>
        </fieldset>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <WaferCanvasPanel
          label="Original Wafer"
          draw={drawOriginal}
          renderSize={RENDER_SIZE}
          legend={baseImage ? undefined : <BinMapLegend />}
          footnote={
            baseImage
              ? "Original wafer image from the analysis pipeline — no overlays applied"
              : "Raw wafer bin map — no overlays applied"
          }
        />
        <WaferCanvasPanel
          label="Failure Overlay"
          draw={drawOverlay}
          renderSize={RENDER_SIZE}
          legend={<OverlayLegend />}
          onPick={onPickDie}
          controls={
            <label className="ml-auto flex items-center gap-1.5 text-[10px] text-slate-400">
              Markers {Math.round(markerAlpha * 100)}%
              <input
                type="range"
                min={0.2}
                max={1}
                step={0.05}
                value={markerAlpha}
                onChange={(e) => setMarkerAlpha(Number(e.target.value))}
                className="w-16 accent-[#DC3232]"
              />
            </label>
          }
          footnote={
            selectedDie
              ? `Die ${selectedDie.die_id ?? selectedDie.id} · R${selectedDie.row}/C${selectedDie.column} · ${selectedDie.status}`
              : "1px die outlines — green GOOD, red FAIL — over the wafer boundary"
          }
        />
        <WaferCanvasPanel
          label="Failure Density Map"
          draw={drawDensity}
          renderSize={RENDER_SIZE}
          legend={<DensityLegend />}
          controls={
            <label className="ml-auto flex items-center gap-1.5 text-[10px] text-slate-400">
              Intensity {Math.round(densityIntensity * 100)}%
              <input
                type="range"
                min={0.6}
                max={1.4}
                step={0.05}
                value={densityIntensity}
                onChange={(e) => setDensityIntensity(Number(e.target.value))}
                className="w-16 accent-[#F97316]"
              />
            </label>
          }
          footnote={`JSON KDE · ${visualization.density.points.length} FAIL points · σ ${visualization.density.sigma.toFixed(2)}`}
        />
        <AiAttentionPanel
          gradcam={visualization.gradcam}
          density={visualization.density}
          coordinateSpace={visualization.coordinate_space}
          meta={selected?.gradcam_meta}
          wafer={wafer}
        />
      </div>
    </section>
  );
}
