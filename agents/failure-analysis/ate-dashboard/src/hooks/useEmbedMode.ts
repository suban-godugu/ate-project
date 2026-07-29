"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

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
  const pathname = usePathname();
  const [embed, setEmbed] = useState(detectEmbed);

  useEffect(() => {
    const active = detectEmbed();
    setEmbed(active);
    applyEmbedClass(active);
  }, [pathname]);

  useEffect(() => {
    applyEmbedClass(embed);
  }, [embed]);

  return embed;
}

/** Keep `?embed=1` on in-app links while embedded in VERILUMEN. */
export function withEmbedQuery(href: string, embed: boolean): string {
  if (!embed) return href;
  try {
    const url = new URL(href, "http://local.invalid");
    url.searchParams.set("embed", "1");
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return href.includes("?") ? `${href}&embed=1` : `${href}?embed=1`;
  }
}
