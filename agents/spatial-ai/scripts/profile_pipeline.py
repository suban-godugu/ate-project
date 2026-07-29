"""
Lightweight pipeline timing profile (ops aid — does not change AI logic).

Usage:
    python -m scripts.profile_pipeline [optional_image_path]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    from src.wafer_pipeline import run_wafer_analysis

    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        image = Path(args[0])
    else:
        matches = list((ROOT / "wafer dataset" / "data" / "test").rglob("*.jpg"))
        if not matches:
            print("No sample image found.")
            return 1
        image = matches[0]

    print(f"Profiling: {image}")
    started = time.perf_counter()
    result = run_wafer_analysis(image, save_log=False, include_images=True)
    total_ms = (time.perf_counter() - started) * 1000.0

    timing = result.get("timing_ms") or {}
    spatial = result.get("spatial_analysis") or {}
    print(f"total_wall_ms     : {total_ms:.1f}")
    print(f"pipeline_timing   : {timing}")
    if spatial:
        print(
            "clusters_displayed:",
            spatial.get("cluster_summary", {}).get("displayed_clusters"),
        )
        print("zones            :", len(spatial.get("zone_analysis") or []))
    print("NOTE: Optimize infrastructure only — do not alter prediction math.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
