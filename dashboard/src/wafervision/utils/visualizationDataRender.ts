import type {
  VisualizationColorStop,
  VisualizationDensity,
  VisualizationGradcam,
} from "@/wafervision/types";

const BLACK = "#080d17";

function hexRgb(hex: string): [number, number, number] {
  const value = hex.replace("#", "");
  const full = value.length === 3
    ? value.split("").map((c) => c + c).join("")
    : value;
  const n = Number.parseInt(full, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function gaussianKernel(sigma: number): Float32Array {
  const radius = Math.max(1, Math.ceil(sigma * 3));
  const kernel = new Float32Array(radius * 2 + 1);
  const denominator = 2 * sigma * sigma;
  let sum = 0;
  for (let i = -radius; i <= radius; i += 1) {
    const value = Math.exp(-(i * i) / denominator);
    kernel[i + radius] = value;
    sum += value;
  }
  for (let i = 0; i < kernel.length; i += 1) kernel[i] /= sum;
  return kernel;
}

function gaussianBlur(field: Float32Array, width: number, height: number, sigma: number): Float32Array {
  const kernel = gaussianKernel(Math.max(0.5, sigma));
  const radius = (kernel.length - 1) / 2;
  const horizontal = new Float32Array(width * height);
  const output = new Float32Array(width * height);

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      let value = 0;
      for (let k = -radius; k <= radius; k += 1) {
        const sx = x + k;
        if (sx >= 0 && sx < width) {
          value += field[y * width + sx] * kernel[k + radius];
        }
      }
      horizontal[y * width + x] = value;
    }
  }

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      let value = 0;
      for (let k = -radius; k <= radius; k += 1) {
        const sy = y + k;
        if (sy >= 0 && sy < height) {
          value += horizontal[sy * width + x] * kernel[k + radius];
        }
      }
      output[y * width + x] = value;
    }
  }
  return output;
}

function bilinear(
  values: Float32Array | number[],
  width: number,
  height: number,
  x: number,
  y: number,
): number {
  const px = Math.max(0, Math.min(width - 1, x));
  const py = Math.max(0, Math.min(height - 1, y));
  const x0 = Math.floor(px);
  const y0 = Math.floor(py);
  const x1 = Math.min(width - 1, x0 + 1);
  const y1 = Math.min(height - 1, y0 + 1);
  const fx = px - x0;
  const fy = py - y0;
  const top = values[y0 * width + x0] * (1 - fx) + values[y0 * width + x1] * fx;
  const bottom = values[y1 * width + x0] * (1 - fx) + values[y1 * width + x1] * fx;
  return top * (1 - fy) + bottom * fy;
}

function interpolateColor(value: number, stops: VisualizationColorStop[]): [number, number, number] {
  const sorted = stops.length
    ? [...stops].sort((a, b) => a.at - b.at)
    : [
        { at: 0, color: "#1D4ED8" },
        { at: 0.3, color: "#16A34A" },
        { at: 0.58, color: "#FACC15" },
        { at: 1, color: "#DC2626" },
      ];
  const t = Math.max(0, Math.min(1, value));
  for (let i = 1; i < sorted.length; i += 1) {
    if (t <= sorted[i].at) {
      const left = sorted[i - 1];
      const right = sorted[i];
      const amount = (t - left.at) / Math.max(1e-6, right.at - left.at);
      const a = hexRgb(left.color);
      const b = hexRgb(right.color);
      return [
        Math.round(a[0] + (b[0] - a[0]) * amount),
        Math.round(a[1] + (b[1] - a[1]) * amount),
        Math.round(a[2] + (b[2] - a[2]) * amount),
      ];
    }
  }
  return hexRgb(sorted[sorted.length - 1].color);
}

function scalarCanvas(
  values: Float32Array | number[],
  fieldWidth: number,
  fieldHeight: number,
  outputSize: number,
  colorStops: VisualizationColorStop[],
  floor: number,
  mask?: { center_x: number; center_y: number; radius: number },
): HTMLCanvasElement {
  // 512 scalar samples are enough for smooth display while keeping redraws
  // responsive. The resulting canvas is then GPU-scaled to the backing store.
  const rasterSize = Math.min(512, outputSize);
  const canvas = document.createElement("canvas");
  canvas.width = rasterSize;
  canvas.height = rasterSize;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;
  const image = ctx.createImageData(rasterSize, rasterSize);

  for (let y = 0; y < rasterSize; y += 1) {
    for (let x = 0; x < rasterSize; x += 1) {
      const fieldX = (x / Math.max(1, rasterSize - 1)) * (fieldWidth - 1);
      const fieldY = (y / Math.max(1, rasterSize - 1)) * (fieldHeight - 1);
      const index = (y * rasterSize + x) * 4;

      if (
        mask &&
        (fieldX - mask.center_x) ** 2 + (fieldY - mask.center_y) ** 2 > mask.radius ** 2
      ) {
        image.data[index + 3] = 0;
        continue;
      }

      const raw = bilinear(values, fieldWidth, fieldHeight, fieldX, fieldY);
      if (raw <= 0) {
        image.data[index + 3] = 0;
        continue;
      }
      const normalized = Math.pow(Math.min(1, raw), 0.85);
      // Fade the weakest tail out instead of clipping it, which is what turned
      // separate hotspots into solid islands with hard edges.
      const fade = floor > 0 ? Math.min(1, raw / floor) : 1;
      const [r, g, b] = interpolateColor(normalized, colorStops);
      image.data[index] = r;
      image.data[index + 1] = g;
      image.data[index + 2] = b;
      image.data[index + 3] = Math.round(255 * fade * fade);
    }
  }
  ctx.putImageData(image, 0, 0);
  return canvas;
}

/** Render backend-provided KDE parameters and FAIL points at canvas resolution. */
export function drawDensityData(
  ctx: CanvasRenderingContext2D,
  size: number,
  density: VisualizationDensity,
  coordinateWidth: number,
  coordinateHeight: number,
  intensity = 1,
): void {
  ctx.fillStyle = BLACK;
  ctx.fillRect(0, 0, size, size);

  const raw = new Float32Array(coordinateWidth * coordinateHeight);
  for (const point of density.points) {
    const x = Math.round(point.x);
    const y = Math.round(point.y);
    if (x >= 0 && x < coordinateWidth && y >= 0 && y < coordinateHeight) {
      raw[y * coordinateWidth + x] += point.weight;
    }
  }
  const smoothed = gaussianBlur(raw, coordinateWidth, coordinateHeight, density.sigma);
  let maximum = 0;
  for (let i = 0; i < smoothed.length; i += 1) maximum = Math.max(maximum, smoothed[i]);
  if (maximum <= 0) return;
  for (let i = 0; i < smoothed.length; i += 1) {
    smoothed[i] = Math.min(1, (smoothed[i] / maximum) * intensity);
  }

  const heatmap = scalarCanvas(
    smoothed,
    coordinateWidth,
    coordinateHeight,
    size,
    density.color_stops,
    density.floor,
    density.mask,
  );
  ctx.save();
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(heatmap, 0, 0, size, size);
  ctx.restore();

  drawMaskOutline(ctx, size, density.mask, coordinateWidth);
}

/** Faint wafer edge so hotspots read against the wafer, not empty space. */
function drawMaskOutline(
  ctx: CanvasRenderingContext2D,
  size: number,
  mask: VisualizationDensity["mask"],
  coordinateWidth: number,
): void {
  if (!mask) return;
  const scale = size / coordinateWidth;
  ctx.save();
  ctx.strokeStyle = "rgba(148, 163, 184, 0.35)";
  ctx.lineWidth = Math.max(1, size / 1024);
  ctx.beginPath();
  ctx.arc(mask.center_x * scale, mask.center_y * scale, mask.radius * scale, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

/** Blend the backend-provided native CAM scalar grid over the rendered wafer. */
export function drawGradcamData(
  ctx: CanvasRenderingContext2D,
  size: number,
  gradcam: VisualizationGradcam,
  opacity: number,
): void {
  const heatmap = gradcam.heatmap;
  if (!gradcam.available || !heatmap || heatmap.values.length !== heatmap.width * heatmap.height) {
    return;
  }
  const canvas = scalarCanvas(
    heatmap.values,
    heatmap.width,
    heatmap.height,
    size,
    [
      { at: 0, color: "#1D4ED8" },
      { at: 0.35, color: "#22C55E" },
      { at: 0.65, color: "#FACC15" },
      { at: 1, color: "#DC2626" },
    ],
    0,
  );
  ctx.save();
  ctx.globalAlpha = opacity;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(canvas, 0, 0, size, size);
  ctx.restore();
}
