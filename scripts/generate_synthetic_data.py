#!/usr/bin/env python
"""Generate synthetic fibrosis benchmark arrays under data/synthetic/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.constants import D_HEALTHY_MM2_PER_MS, LAMBDA_HEALTHY
from cardiac_ms.tissue_classes import disk_fibrosis_three_class, fibrosis_mask

OUT_DIR = ROOT / "data" / "synthetic"


def build_patch(nx: int = 64, ny: int = 64) -> dict:
    center = (nx // 2, ny // 2)
    radius = max(2, nx // 8)
    mask = fibrosis_mask(nx, ny, center=center, radius=radius)
    D_normal = float(D_HEALTHY_MM2_PER_MS)
    D_fibrosis = D_normal * 0.10
    D = np.where(mask, D_fibrosis, D_normal).astype(np.float64)
    three = disk_fibrosis_three_class(
        nx,
        ny,
        center=center,
        radius=radius,
        border_width=2,
        D_healthy=D_normal,
        d_reduction_dense=0.90,
        lam_healthy=LAMBDA_HEALTHY,
        lam_dense=0.2,
    )
    return {
        "nx": nx,
        "ny": ny,
        "center": list(center),
        "radius": radius,
        "D_normal_mm2_per_ms": D_normal,
        "D_fibrosis_mm2_per_ms": D_fibrosis,
        "mask": mask,
        "D": D,
        "three": three,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spec = build_patch(64, 64)
    np.save(OUT_DIR / "fibrosis_patch_64_mask.npy", spec["mask"])
    np.save(OUT_DIR / "fibrosis_patch_64_D.npy", spec["D"])
    three = spec["three"]
    np.save(OUT_DIR / "fibrosis_patch_64_classes.npy", three.classes)
    np.save(OUT_DIR / "fibrosis_patch_64_lam.npy", three.lam)

    meta = {
        "description": "Synthetic 64x64 fibrosis disk for mono2d benchmarks (binary + three-class)",
        "nx": spec["nx"],
        "ny": spec["ny"],
        "units": {
            "space": "mm (grid index * dx)",
            "D": "mm^2/ms",
            "time": "ms",
            "u": "dimensionless",
            "lambda": "dimensionless",
        },
        "geometry": {
            "center_ij": spec["center"],
            "radius_cells": spec["radius"],
            "fibrosis_fraction": float(spec["mask"].mean()),
            "border_width_px": 2,
            "border_fraction": float(three.border_mask.mean()),
        },
        "conductivity": {
            "D_normal_mm2_per_ms": spec["D_normal_mm2_per_ms"],
            "D_fibrosis_mm2_per_ms": spec["D_fibrosis_mm2_per_ms"],
            "ratio_normal_to_fibrosis": spec["D_normal_mm2_per_ms"]
            / spec["D_fibrosis_mm2_per_ms"],
        },
        "modified_ms": {
            "lambda_healthy": LAMBDA_HEALTHY,
            "lambda_dense": 0.2,
        },
        "files": {
            "mask": "fibrosis_patch_64_mask.npy",
            "D": "fibrosis_patch_64_D.npy",
            "classes": "fibrosis_patch_64_classes.npy",
            "lam": "fibrosis_patch_64_lam.npy",
        },
    }
    (OUT_DIR / "fibrosis_patch_64.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_DIR} ({meta['geometry']['fibrosis_fraction']:.3%} fibrotic)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
