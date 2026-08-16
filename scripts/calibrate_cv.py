#!/usr/bin/env python
"""Calibrate monodomain D so homogeneous 2D CV ≈ 0.7 mm/ms (paper target)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.validation import calibrate_healthy_diffusion, measure_homogeneous_cv
from cardiac_ms.constants import D_HEALTHY_MM2_PER_MS, CV_TARGET_MM_PER_MS


def main() -> int:
    print(f"Current D_HEALTHY_MM2_PER_MS = {D_HEALTHY_MM2_PER_MS}")
    print(f"Target CV = {CV_TARGET_MM_PER_MS} mm/ms")
    result = calibrate_healthy_diffusion()
    print(json.dumps(result, indent=2, default=str))
    d_star = result.get("D_star")
    if d_star is not None:
        check = measure_homogeneous_cv(d_star)
        print(f"\nRecommended D = {d_star:.6f} mm^2/ms")
        print(f"Measured CV   = {check['cv_mm_per_ms']} mm/ms  u_max={check['u_max']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
