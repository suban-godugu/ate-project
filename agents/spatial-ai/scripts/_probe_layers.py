import base64
import time
from pathlib import Path

import cv2
import httpx
import numpy as np

cands = list(Path(r"C:\personal\input all file").rglob("*.png")) + list(
    Path(r"C:\personal\input all file").rglob("*.jpg")
)
cands = [p for p in cands if p.stat().st_size > 2000]
p = cands[0] if cands else None
if p is None:
    img = np.zeros((224, 224, 3), np.uint8)
    cv2.circle(img, (112, 112), 100, (40, 160, 80), -1)
    for i in range(20):
        cv2.circle(img, (60 + i * 5, 80 + i * 3), 3, (220, 50, 50), -1)
    p = Path(r"C:\personal\input all file\_spatial_test.png")
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

print("using", p, p.stat().st_size)
t = time.perf_counter()
r = httpx.post(
    "http://127.0.0.1:8006/predict",
    files={"image": (p.name, p.read_bytes(), "image/png")},
    data={"grid_mode": "automatic"},
    timeout=180,
)
print("status", r.status_code, f"{(time.perf_counter() - t) * 1000:.0f}ms")
if r.status_code != 200:
    print(r.text[:600])
    raise SystemExit(1)
j = r.json()
imgs = j.get("images") or {}
for k in ("original", "overlay", "density", "gradcam"):
    b = imgs.get(k) or ""
    raw = base64.b64decode(b) if b else b""
    print(k, "png_bytes", len(raw), "png_ok", raw[:8] == b"\x89PNG\r\n\x1a\n")
print("defect", (j.get("classification") or {}).get("defect_type"))
