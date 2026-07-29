import { AGENT_IMAGE_SIZE } from "@/wafervision/constants";
import type {
  ClusterRecord,
  DieRecord,
  GridInfo,
  WaferGeometry,
} from "@/wafervision/types";

/** Enterprise wafer palette (KLA/PDF-style bin map). */
export const WAFER_COLORS = {
  background: "#080d17",
  waferBase: "#0d2b33",
  good: "#14A8A8",
  fail: "#F2C222",
  failOverlayBorder: "#FF4D4D",
  selected: "#FDE047",
  cluster: "#FB923C",
  boundary: "#FFFFFF",
  /** Agent overlay die outlines: cv2 (40,180,90) and (220,50,50). */
  goodOutline: "#28B45A",
  failOutline: "#DC3232",
} as const;

export interface WaferRenderInput {
  dies: DieRecord[];
  geometry?: WaferGeometry | null;
  gridInfo?: GridInfo | null;
  /** Agent's original wafer PNG; drawn as the base layer when decoded. */
  image?: CanvasImageSource | null;
}

interface DieRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

function isFail(die: DieRecord): boolean {
  return String(die.status ?? "").toUpperCase() === "FAIL";
}

function pitchOf(gridInfo?: GridInfo | null): number {
  const pitch = Number(gridInfo?.pitch);
  return Number.isFinite(pitch) && pitch > 0 ? pitch : 4.5;
}

/**
 * Die cell rect in display pixels. Uses agent bbox when present so overlay
 * markers land exactly on the die lattice at any render size.
 */
function dieRect(die: DieRecord, scale: number, pitch: number): DieRect | null {
  const bbox = die.bbox;
  if (bbox && bbox.x1 != null && bbox.x0 != null && bbox.y0 != null && bbox.y1 != null) {
    const x = Math.round(bbox.x0 * scale);
    const y = Math.round(bbox.y0 * scale);
    return {
      x,
      y,
      w: Math.max(1, Math.round(bbox.x1 * scale) - x),
      h: Math.max(1, Math.round(bbox.y1 * scale) - y),
    };
  }

  if (die.x == null || die.y == null) return null;
  const half = (pitch / 2) * scale;
  const x = Math.round(die.x * scale - half);
  const y = Math.round(die.y * scale - half);
  return {
    x,
    y,
    w: Math.max(1, Math.round(half * 2)),
    h: Math.max(1, Math.round(half * 2)),
  };
}

function paintBackground(
  ctx: CanvasRenderingContext2D,
  size: number,
  geometry: WaferGeometry | null | undefined,
  scale: number,
): void {
  ctx.fillStyle = WAFER_COLORS.background;
  ctx.fillRect(0, 0, size, size);

  const cx = (geometry?.center_x ?? AGENT_IMAGE_SIZE / 2) * scale;
  const cy = (geometry?.center_y ?? AGENT_IMAGE_SIZE / 2) * scale;
  const r = (geometry?.radius ?? AGENT_IMAGE_SIZE / 2) * scale;

  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = WAFER_COLORS.waferBase;
  ctx.fill();
}

/**
 * Base wafer layer: the agent's original wafer image when available, otherwise
 * a synthesized bin map (cyan good dies, yellow fail dies).
 */
export function drawOriginalWafer(
  ctx: CanvasRenderingContext2D,
  size: number,
  { dies, geometry, gridInfo, image }: WaferRenderInput,
): void {
  if (image) {
    ctx.fillStyle = WAFER_COLORS.background;
    ctx.fillRect(0, 0, size, size);
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(image, 0, 0, size, size);
    ctx.restore();
    return;
  }

  const scale = size / AGENT_IMAGE_SIZE;
  const pitch = pitchOf(gridInfo);
  paintBackground(ctx, size, geometry, scale);

  for (const die of dies) {
    const rect = dieRect(die, scale, pitch);
    if (!rect) continue;
    ctx.fillStyle = isFail(die) ? WAFER_COLORS.fail : WAFER_COLORS.good;
    ctx.fillRect(rect.x, rect.y, rect.w, rect.h);
  }
}

/** White wafer boundary circle, matching the agent's overlay rendering. */
function drawWaferBoundary(
  ctx: CanvasRenderingContext2D,
  size: number,
  geometry: WaferGeometry | null | undefined,
  scale: number,
): void {
  const cx = (geometry?.center_x ?? AGENT_IMAGE_SIZE / 2) * scale;
  const cy = (geometry?.center_y ?? AGENT_IMAGE_SIZE / 2) * scale;
  const r = (geometry?.radius ?? AGENT_IMAGE_SIZE / 2) * scale;

  ctx.save();
  ctx.strokeStyle = WAFER_COLORS.boundary;
  ctx.lineWidth = Math.max(1, size / 512);
  ctx.beginPath();
  ctx.arc(cx, cy, Math.max(r - ctx.lineWidth, 1), 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

export interface OverlayOptions extends WaferRenderInput {
  selectedDieId?: number | string | null;
  clusters?: ClusterRecord[];
  /** Opacity of the marker layer; 1 reproduces the agent overlay exactly. */
  markerAlpha?: number;
  showClusters?: boolean;
}

/**
 * Failure overlay in the agent's style: original wafer, white boundary circle,
 * and a 1 px outline on every die — green for GOOD, red for FAIL — plus the
 * dashboard's selected-die and cluster highlights.
 */
export function drawFailureOverlay(
  ctx: CanvasRenderingContext2D,
  size: number,
  {
    dies,
    geometry,
    gridInfo,
    image,
    selectedDieId = null,
    clusters = [],
    markerAlpha = 1,
    showClusters = true,
  }: OverlayOptions,
): void {
  const scale = size / AGENT_IMAGE_SIZE;
  const pitch = pitchOf(gridInfo);
  drawOriginalWafer(ctx, size, { dies, geometry, gridInfo, image });
  drawWaferBoundary(ctx, size, geometry, scale);

  const border = Math.max(1, Math.round(size / 1024));
  // The agent insets each marker by one model pixel so neighbouring outlines
  // never merge into a solid mesh.
  const inset = Math.max(border, Math.round(scale));
  let selectedRect: DieRect | null = null;

  ctx.save();
  ctx.globalAlpha = markerAlpha;
  ctx.lineWidth = border;

  for (const die of dies) {
    const rect = dieRect(die, scale, pitch);
    if (!rect) continue;
    const id = die.die_id ?? die.id;
    if (selectedDieId != null && id != null && String(id) === String(selectedDieId)) {
      selectedRect = rect;
    }
    const w = rect.w - inset * 2;
    const h = rect.h - inset * 2;
    if (w <= 0 || h <= 0) continue;
    ctx.strokeStyle = isFail(die) ? WAFER_COLORS.failOutline : WAFER_COLORS.goodOutline;
    ctx.strokeRect(rect.x + inset, rect.y + inset, w, h);
  }
  ctx.restore();

  if (showClusters && clusters.length) {
    ctx.save();
    ctx.strokeStyle = WAFER_COLORS.cluster;
    ctx.lineWidth = Math.max(1.5, size / 640);
    ctx.setLineDash([size / 128, size / 200]);
    for (const cluster of clusters) {
      const box = cluster.bounding_box;
      const tuple = cluster.bbox;
      let x0: number, y0: number, x1: number, y1: number;
      if (box?.x1 != null && box?.y1 != null && box?.x2 != null && box?.y2 != null) {
        x0 = Number(box.x1);
        y0 = Number(box.y1);
        x1 = Number(box.x2);
        y1 = Number(box.y2);
      } else if (tuple) {
        [x0, y0, x1, y1] = tuple;
      } else {
        continue;
      }
      ctx.strokeRect(x0 * scale, y0 * scale, (x1 - x0) * scale, (y1 - y0) * scale);
    }
    ctx.restore();
  }

  if (selectedRect) {
    ctx.save();
    ctx.strokeStyle = WAFER_COLORS.selected;
    ctx.lineWidth = Math.max(2, size / 512);
    ctx.strokeRect(selectedRect.x, selectedRect.y, selectedRect.w, selectedRect.h);
    ctx.restore();
  }
}

/** Nearest die to a point given in agent (224) space. */
export function pickDie(
  dies: DieRecord[],
  agentX: number,
  agentY: number,
  maxDistance = 6,
): DieRecord | null {
  let best: DieRecord | null = null;
  let bestDist = Number.POSITIVE_INFINITY;
  for (const die of dies) {
    if (die.x == null || die.y == null) continue;
    const d = (die.x - agentX) ** 2 + (die.y - agentY) ** 2;
    if (d < bestDist) {
      bestDist = d;
      best = die;
    }
  }
  return bestDist <= maxDistance * maxDistance ? best : null;
}
