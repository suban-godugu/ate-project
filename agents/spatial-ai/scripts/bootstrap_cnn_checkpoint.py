"""Bootstrap a real ResNet50 wafer checkpoint (ImageNet backbone + 9-class head).

Replaces Git-LFS pointer files so Grad-CAM / predict can run with CNN weights.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.model import WaferClassifier, save_model
from src.wafer_constants import DEFECT_CLASSES

OUT = ROOT / "models" / "resnet50_layer4_ft.pth"
ALT = ROOT / "models" / "wafer_model.pth"


def main() -> None:
    print(f"Building WaferClassifier ({len(DEFECT_CLASSES)} classes) with ImageNet backbone…")
    model = WaferClassifier(
        pretrained=True,
        freeze_backbone=True,
        unfreeze_layer4=True,
    )
    model.eval()
    path = save_model(OUT, model, epoch=0, val_accuracy=0.0, val_loss=0.0, wafer_trained=False)
    save_model(ALT, model, epoch=0, val_accuracy=0.0, val_loss=0.0, wafer_trained=False)
    print(f"Wrote CNN checkpoint: {path} ({path.stat().st_size / 1e6:.1f} MB) wafer_trained=False")
    print(f"Wrote alias: {ALT} ({ALT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
