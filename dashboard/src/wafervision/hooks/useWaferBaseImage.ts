"use client";

import { useEffect, useState } from "react";
import { toDataUrl } from "@/wafervision/utils/format";

/**
 * Decode the agent's original wafer PNG into an image usable as a canvas base
 * layer. Panels draw vector overlays on top of it, so the wafer photo itself is
 * never replaced by synthesized die colors.
 */
export function useWaferBaseImage(base64?: string | null): HTMLImageElement | null {
  const [image, setImage] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    const src = toDataUrl(base64);
    if (!src) {
      setImage(null);
      return;
    }

    let active = true;
    const element = new Image();
    element.onload = () => {
      if (active) setImage(element);
    };
    element.onerror = () => {
      if (active) setImage(null);
    };
    element.src = src;

    return () => {
      active = false;
    };
  }, [base64]);

  return image;
}
