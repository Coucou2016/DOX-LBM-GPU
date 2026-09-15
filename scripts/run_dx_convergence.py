#!/usr/bin/env python
"""
Spatial (dx) and temporal (dt) convergence checks for the 2D monodomain scaffold.

dx sweep: {0.75, 0.5, 0.25} mm at dt=0.1 ms (CFL-enforced).
dt sweep: {0.1, 0.05, 0.025} ms at fixed dx=0.5 mm.

Writes data/dx_convergence.csv and data/dt_convergence.csv.
These are numerical verification artefacts, not biological claims.

Also records 0D APD, wavelength proxy (CV×APD), and an annulus lap-period
estimate (path/CV) plus a pointer to VA labels at the default annulus dx.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.constants import D_HEALTHY_MM2_PER_MS, LAMBDA_HEALTHY
from cardiac_ms.geometries import default_annulus_spec
from cardiac_ms.ms_0d import measure_apd
from cardiac_ms.ms_2d import simulate_mono2d
from cardiac_ms.ms_modified import get_modified_parameters, simulate_ms_0d_modified

# Default verification-ring path (mm); used only for cheap lap estimates.
_ANNULUS_PATH_MM = float(default_annulus_spec()["path_mm"])
_VA_NOTE = (
    "VA labels at default annulus dx=0.75 mm are in papers/data/phase_diagram.csv "
    "(full 4×3); this sweep does not reclassify VA per dx (homogeneous CV only)."
)


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


def _enrich_row(row: dict, apd0: float | None) -> dict:
    row["apd0d_ms"] = apd0
    cv = row.get("cv_mm_per_ms")
    try:
        cv_f = float(cv) if cv is not None else None
    except (TypeError, ValueError):
        cv_f = None
    if apd0 and cv_f and cv_f > 0:
        row["wavelength_mm"] = float(cv_f) * float(apd0)
        row["annulus_lap_est_ms"] = _ANNULUS_PATH_MM / float(cv_f)
    else:
        row["wavelength_mm"] = None
        row["annulus_lap_est_ms"] = None
    row["va_classification_note"] = _VA_NOTE
    return row


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
            row = _enrich_row(measure_cv(dx=float(dx), dt=0.1), apd0)
            dx_rows.append(row)
            print(
                f"dx={row['dx_mm']}  CV={row['cv_mm_per_ms']}  "
                f"λ_wave={row.get('wavelength_mm')}  "
                f"lap_est={row.get('annulus_lap_est_ms')}  "
                f"u_max={row['u_max']:.3f}  ({row['elapsed_s']:.1f}s)"
            )
        dx_path = out_dir / "dx_convergence.csv"
        write_csv(dx_path, dx_rows)
        mirror = ROOT / "outputs" / "dx_convergence.csv"
        mirror.parent.mkdir(parents=True, exist_ok=True)
        write_csv(mirror, dx_rows)
        (out_dir / "dx_convergence_note.json").write_text(
            json.dumps({"va_classification_note": _VA_NOTE, "apd0d_ms": apd0}, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {dx_path}")

    if not args.skip_dt:
        dt_rows = []
        for dt in args.dt:
            row = _enrich_row(measure_cv(dx=0.5, dt=float(dt)), apd0)
            dt_rows.append(row)
            print(
                f"dt={row['dt_requested_ms']} (used {row['dt_ms']})  "
                f"CV={row['cv_mm_per_ms']}  λ_wave={row.get('wavelength_mm')}  "
                f"u_max={row['u_max']:.3f}  ({row['elapsed_s']:.1f}s)"
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
