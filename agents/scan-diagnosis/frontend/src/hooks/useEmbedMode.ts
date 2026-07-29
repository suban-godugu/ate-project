"use client";

import { useEffect, useState } from "react";

const EMBED_STORAGE_KEY = "verilumen_platform_embed";

function applyEmbedClass(active: boolean) {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("embed", active);
  document.body.classList.toggle("embed", active);
}

function detectEmbed(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const params = new URLSearchParams(window.location.search);
    const flag = params.get("embed");
    if (flag === "1" || flag === "true") {
      sessionStorage.setItem(EMBED_STORAGE_KEY, "1");
      return true;
    }
    if (sessionStorage.getItem(EMBED_STORAGE_KEY) === "1") {
      return true;
    }
    // VERILUMEN loads this app in an iframe — never show full agent chrome there.
    if (window.self !== window.top) {
      sessionStorage.setItem(EMBED_STORAGE_KEY, "1");
      return true;
    }
    return false;
  } catch {
    // Cross-origin iframe access can throw; treat as embed.
    return true;
  }
}

/** True when loaded inside VERILUMEN Scan Chain iframe (`?embed=1`). */
export function useEmbedMode(): boolean {
  const [embed, setEmbed] = useState(detectEmbed);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const active = detectEmbed();
    setEmbed(active);
    applyEmbedClass(active);
    setReady(true);
  }, []);

  useEffect(() => {
    applyEmbedClass(embed);
  }, [embed]);

  return embed;
}

/** Avoid painting full header for one frame before embed is known. */
export function useEmbedReady(): boolean {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    setReady(true);
  }, []);
  return ready;
}
