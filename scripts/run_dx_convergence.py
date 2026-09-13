#!/usr/bin/env python
"""
Spatial (dx) and temporal (dt) convergence checks for the 2D monodomain scaffold.

dx sweep: {0.75, 0.5, 0.25} mm at dt=0.1 ms (CFL-enforced).
dt sweep: {0.1, 0.05, 0.025} ms at fixed dx=0.5 mm.

Writes data/dx_convergence.csv and data/dt_convergence.csv.
These are numerical verification artefacts, not biological claims.
"""

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


def measure_cv(
    *,
    dx: float,
    dt: float,
    domain_mm: float = 24.0,
    t_end_ms: float = 800.0,
) -> dict:
    nx = max(16, int(round(domain_mm / dx)))
    ny = nx
    n_steps = int(t_end_ms / dt)
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
        stimulus_mode="current",
        stim_u=0.8,
    )
    return {
        "dx_mm": dx,
        "dt_ms": meta["dt"],
        "dt_requested_ms": dt,
        "nx": nx,
        "ny": ny,
        "cv_mm_per_ms": meta.get("cv_mm_per_ms"),
        "u_max": float(meta.get("u_peak") or u.max()),
        "cfl_r": meta["cfl_r"],
        "dt_clamped": bool(meta.get("dt_clamped")),
        "elapsed_s": meta["elapsed_s"],
    }


def measure_0d_apd() -> float | None:
    p = get_modified_parameters(lam=LAMBDA_HEALTHY)
    t, u, _ = simulate_ms_0d_modified(n_steps=5000, dt=0.1, params=p)
    return measure_apd(t, u).get("apd_ms")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dx", type=float, nargs="+", default=[0.75, 0.5, 0.25])
    ap.add_argument("--dt", type=float, nargs="+", default=[0.1, 0.05, 0.025])
    ap.add_argument("--skip-dx", action="store_true")
    ap.add_argument("--skip-dt", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data")
    args = ap.parse_args()

    apd0 = measure_0d_apd()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_dx:
        dx_rows = []
        for dx in args.dx:
            row = measure_cv(dx=float(dx), dt=0.1)
            row["apd0d_ms"] = apd0
            dx_rows.append(row)
            print(
                f"dx={row['dx_mm']}  CV={row['cv_mm_per_ms']}  "
                f"u_max={row['u_max']:.3f}  ({row['elapsed_s']:.1f}s)"
            )
        dx_path = out_dir / "dx_convergence.csv"
        write_csv(dx_path, dx_rows)
        mirror = ROOT / "outputs" / "dx_convergence.csv"
        mirror.parent.mkdir(parents=True, exist_ok=True)
        write_csv(mirror, dx_rows)
        print(f"Wrote {dx_path}")

    if not args.skip_dt:
        dt_rows = []
        for dt in args.dt:
            row = measure_cv(dx=0.5, dt=float(dt))
            row["apd0d_ms"] = apd0
            dt_rows.append(row)
            print(
                f"dt={row['dt_requested_ms']} (used {row['dt_ms']})  "
                f"CV={row['cv_mm_per_ms']}  u_max={row['u_max']:.3f}  "
                f"({row['elapsed_s']:.1f}s)"
            )
        dt_path = out_dir / "dt_convergence.csv"
        write_csv(dt_path, dt_rows)
        mirror = ROOT / "outputs" / "dt_convergence.csv"
        mirror.parent.mkdir(parents=True, exist_ok=True)
        write_csv(mirror, dt_rows)
        print(f"Wrote {dt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
