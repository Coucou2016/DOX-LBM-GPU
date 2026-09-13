#!/usr/bin/env python
"""Minimal dx convergence: report CV / APD-like metrics for dx in {0.75, 0.5, 0.25}."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.constants import D_HEALTHY_MM2_PER_MS, LAMBDA_HEALTHY
from cardiac_ms.ms_0d import measure_apd
from cardiac_ms.ms_2d import simulate_mono2d
from cardiac_ms.ms_modified import get_modified_parameters, simulate_ms_0d_modified


def measure_cv(dx: float, *, domain_mm: float = 24.0, dt: float = 0.1) -> dict:
    nx = max(16, int(round(domain_mm / dx)))
    ny = nx
    # Keep physical stim / probe spacing roughly proportional
    n_steps = int(800.0 / dt)
    _, u, _, meta = simulate_mono2d(
        nx=nx,
        ny=ny,
        n_steps=n_steps,
        dt=dt,
        dx=dx,
        fibrosis=False,
        D_normal=D_HEALTHY_MM2_PER_MS,
        lam=LAMBDA_HEALTHY,
        s1_window=(5, 15),
        s2_window=(99999, 999999),
        snapshots=False,
        enforce_cfl=True,
    )
    return {
        "dx_mm": dx,
        "dt_ms": meta["dt"],
        "nx": nx,
        "ny": ny,
        "cv_mm_per_ms": meta.get("cv_mm_per_ms"),
        "u_max": float(meta.get("u_peak") or u.max()),
        "cfl_r": meta["cfl_r"],
        "elapsed_s": meta["elapsed_s"],
    }


def measure_0d_apd() -> float | None:
    p = get_modified_parameters(lam=LAMBDA_HEALTHY)
    t, u, _ = simulate_ms_0d_modified(n_steps=5000, dt=0.1, params=p)
    apd = measure_apd(t, u)
    return apd.get("apd_ms")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dx",
        type=float,
        nargs="+",
        default=[0.75, 0.5, 0.25],
        help="Grid spacings (mm)",
    )
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "dx_convergence.csv")
    args = ap.parse_args()
    apd0 = measure_0d_apd()
    rows = []
    for dx in args.dx:
        row = measure_cv(float(dx))
        row["apd0d_ms"] = apd0
        rows.append(row)
        print(
            f"dx={row['dx_mm']}  CV={row['cv_mm_per_ms']}  "
            f"u_max={row['u_max']:.3f}  ({row['elapsed_s']:.1f}s)"
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # Also mirror under data/ if present
    data_out = ROOT / "data" / "dx_convergence.csv"
    data_out.write_text(args.out.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {args.out} and {data_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
