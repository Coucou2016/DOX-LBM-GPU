#!/usr/bin/env python
"""
Inducibility phase diagram: λ_fib × D_fib reduction → VA / Non-VA.

Default geometry is a **pinned annulus** sized so the circuit path (~107 mm)
sits between healthy wavelength (~175 mm) and D↓90% wavelength (~55 mm).
That yields mixed VA / Non-VA at calibrated healthy τ_close=150 ms.

``--geometry disc`` is the paper-like 2D LGE disk; on a 24 mm sheet it is a
documented negative (wavelength does not fit).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from cardiac_ms.constants import (
    D_HEALTHY_MM2_PER_MS,
    D_REDUCTION_GRID,
    LAMBDA_FIBROTIC_GRID,
    LAMBDA_HEALTHY,
    TAU_CLOSE,
)
from cardiac_ms.geometries import annulus_wavelength_report, default_annulus_spec
from cardiac_ms.protocol_s1s2 import run_annulus_s1s2, run_s1s2
from cardiac_ms.tissue_classes import disk_fibrosis_three_class


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fibrosis excitability–diffusion phase diagram")
    p.add_argument("--full", action="store_true", help="4 λ × 3 D-reduction (slow)")
    p.add_argument("--smoke", action="store_true", help="Two-cell tiny-grid smoke")
    p.add_argument("--geometry", choices=("annulus", "disc"), default="annulus")
    p.add_argument("--nx", type=int, default=None)
    p.add_argument("--ny", type=int, default=None)
    p.add_argument("--dx", type=float, default=None)
    p.add_argument("--out-dir", type=Path, default=ROOT / "outputs")
    return p.parse_args()


def grid_spec(full: bool, smoke: bool, geometry: str) -> dict:
    if smoke:
        return {
            "lam_fib": (0.01, 0.01),
            "d_reduction": (0.30, 0.90),
            "n_s1": 1,
            "extra_cis_ms": (220.0,),
            "observe_ms": 400.0,
            "mode": "smoke",
            "geometry": geometry,
        }
    if full:
        return {
            "lam_fib": LAMBDA_FIBROTIC_GRID,
            "d_reduction": D_REDUCTION_GRID,
            "n_s1": 3,
            "extra_cis_ms": (240.0, 200.0, 190.0),
            "observe_ms": 1000.0,
            "mode": "full",
            "geometry": geometry,
        }
    # Same extras as --full / paper DOX1 train: single CI=220 only yields a
    # one-lap plateau at D↓90% (Non-VA under require_cycle), not mixed labels.
    return {
        "lam_fib": (0.01, 0.3),
        "d_reduction": (0.30, 0.90),
        "n_s1": 3,
        "extra_cis_ms": (240.0, 200.0, 190.0),
        "observe_ms": 1000.0,
        "mode": "fast",
        "geometry": geometry,
    }


def _unique_pairs(lams, reds, smoke: bool) -> list[tuple[float, float]]:
    if smoke:
        return [(0.01, 0.30), (0.01, 0.90)]
    pairs = []
    for lam in lams:
        for d_red in reds:
            pairs.append((float(lam), float(d_red)))
    return pairs


def run_cell_annulus(nx, ny, dx, lam_fib, d_red, spec) -> dict:
    r = run_annulus_s1s2(
        nx=nx,
        ny=ny,
        dx=dx,
        d_reduction=float(d_red),
        lam_ring=float(lam_fib),
        n_s1=spec["n_s1"],
        extra_cis_ms=spec["extra_cis_ms"],
        observe_ms=spec["observe_ms"],
    )
    return {
        "geometry": "annulus",
        "lambda_fib": float(lam_fib),
        "d_reduction": float(d_red),
        "d_fib_frac": 1.0 - float(d_red),
        "label": r["label"],
        "va": 1 if r["label"] == "VA" else 0,
        "activation_persists_ms": r["activation_persists_ms"],
        "n_extra_cycles": r["n_extra_cycles"],
        "n_probes_activated": r.get("n_probes_activated", 0),
        "n_probes_relapped": r.get("n_probes_relapped", 0),
        "excited_fraction": r.get("excited_fraction", 0.0),
        "u_max": r["u_max"],
        "u_final_max": r["u_final_max"],
        "dt": r["dt"],
        "cfl_r": r["cfl_r"],
        "elapsed_s": r["elapsed_s"],
        "n_s1": spec["n_s1"],
        "observe_ms": spec["observe_ms"],
        "nx": nx,
        "ny": ny,
        "dx": dx,
        "path_mm": r.get("path_mm"),
        "tau_close": r.get("tau_close_ring", TAU_CLOSE),
    }


def run_cell_disc(nx, ny, dx, lam_fib, d_red, spec) -> dict:
    tissue = disk_fibrosis_three_class(
        nx,
        ny,
        border_width=2,
        D_healthy=D_HEALTHY_MM2_PER_MS,
        d_reduction_dense=float(d_red),
        d_reduction_border=min(0.50, float(d_red)),
        lam_healthy=LAMBDA_HEALTHY,
        lam_border=0.5 * (LAMBDA_HEALTHY + float(lam_fib)),
        lam_dense=float(lam_fib),
    )
    r = run_s1s2(
        nx=nx,
        ny=ny,
        dx=dx,
        n_s1=spec["n_s1"],
        extra_cis_ms=spec["extra_cis_ms"],
        observe_ms=spec["observe_ms"],
        tissue=tissue,
        s2_cross_field=True,
        dt=0.1,
    )
    return {
        "geometry": "disc",
        "lambda_fib": float(lam_fib),
        "d_reduction": float(d_red),
        "d_fib_frac": 1.0 - float(d_red),
        "label": r["label"],
        "va": 1 if r["label"] == "VA" else 0,
        "activation_persists_ms": r["activation_persists_ms"],
        "n_extra_cycles": r["n_extra_cycles"],
        "n_probes_activated": r.get("n_probes_activated", 0),
        "n_probes_relapped": r.get("n_probes_relapped", 0),
        "excited_fraction": r.get("excited_fraction", 0.0),
        "u_max": r["u_max"],
        "u_final_max": r.get("u_final_max"),
        "dt": r["dt"],
        "cfl_r": r["cfl_r"],
        "elapsed_s": r["elapsed_s"],
        "n_s1": spec["n_s1"],
        "observe_ms": spec["observe_ms"],
        "nx": nx,
        "ny": ny,
        "dx": dx,
        "path_mm": None,
        "tau_close": TAU_CLOSE,
    }


def write_heatmap(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    try:
        from cardiac_ms.plotting import apply_science_style, save_figure

        apply_science_style()
        use_sci = True
    except Exception:
        use_sci = False

    lams = sorted({r["lambda_fib"] for r in rows})
    reds = sorted({r["d_reduction"] for r in rows})
    grid = np.full((len(lams), len(reds)), np.nan)
    for r in rows:
        i = lams.index(r["lambda_fib"])
        j = reds.index(r["d_reduction"])
        grid[i, j] = r["va"]
    fig, ax = plt.subplots(figsize=(3.4, 2.8) if use_sci else (5.2, 4.2))
    im = ax.imshow(grid, origin="lower", vmin=0, vmax=1, cmap="coolwarm", aspect="auto")
    ax.set_xticks(range(len(reds)))
    ax.set_xticklabels([f"{100 * x:.0f}%" for x in reds])
    ax.set_yticks(range(len(lams)))
    ax.set_yticklabels([str(x) for x in lams])
    ax.set_xlabel(r"$D_{\mathrm{fib}}$ reduction" if use_sci else "D_fib reduction")
    ax.set_ylabel(r"$\lambda_{\mathrm{fib}}$" if use_sci else "lambda_fib")
    ax.set_title(f"Inducibility ({rows[0].get('geometry', '')})")
    fig.colorbar(im, ax=ax, fraction=0.046, ticks=[0, 1])
    fig.tight_layout()
    if use_sci:
        stem = out_png.with_suffix("")
        save_figure(fig, stem, dpi=300, formats=("png", "pdf"))
        png = stem.with_suffix(".png")
        if png != out_png:
            import shutil

            shutil.copy2(png, out_png)
    else:
        fig.savefig(out_png, dpi=300)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    spec = grid_spec(args.full, args.smoke, args.geometry)
    ann = default_annulus_spec()
    if args.geometry == "annulus":
        nx = args.nx or (48 if args.smoke else int(ann["nx"]))
        ny = args.ny or nx
        dx = args.dx or (1.0 if args.smoke else float(ann["dx"]))
        r_in, r_out = float(ann["r_in_mm"]), float(ann["r_out_mm"])
        wave = annulus_wavelength_report(r_in_mm=r_in, r_out_mm=r_out, nx=nx, dx=dx)
    else:
        nx = args.nx or 48
        ny = args.ny or nx
        dx = args.dx or 0.5
        wave = None

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pairs = _unique_pairs(spec["lam_fib"], spec["d_reduction"], args.smoke)
    n_total = len(pairs)
    rows = []
    t0 = time.perf_counter()
    print(
        f"Phase diagram mode={spec['mode']} geometry={args.geometry} "
        f"grid={nx}x{ny} dx={dx} cells={n_total}"
    )
    if wave is not None:
        print(wave.note)

    for k, (lam, d_red) in enumerate(pairs, start=1):
        cell_t0 = time.perf_counter()
        if args.geometry == "annulus":
            row = run_cell_annulus(nx, ny, dx, lam, d_red, spec)
        else:
            row = run_cell_disc(nx, ny, dx, lam, d_red, spec)
        rows.append(row)
        print(
            f"[{k}/{n_total}] lam={lam} D↓{100 * d_red:.0f}%  {row['label']}  "
            f"persist={row['activation_persists_ms']:.1f} ms  extra={row['n_extra_cycles']}  "
            f"probes={row.get('n_probes_activated', 0)}  "
            f"relap={row.get('n_probes_relapped', 0)}  "
            f"({time.perf_counter() - cell_t0:.1f}s)"
        )

    elapsed = time.perf_counter() - t0
    csv_path = args.out_dir / "phase_diagram.csv"
    fields = list(rows[0].keys()) if rows else []
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    png = args.out_dir / "phase_diagram.png"
    if rows:
        write_heatmap(rows, png)

    n_va = sum(r["va"] for r in rows)
    n_non = n_total - n_va
    full_expected = None
    if n_total and spec["mode"] == "fast" and args.geometry == "annulus":
        full_expected = (elapsed / n_total) * (4 * 3) * (2430.0 / 1220.0)
    elif n_total and spec["mode"] != "full":
        full_expected = (elapsed / n_total) * 12.0

    summary = {
        "mode": spec["mode"],
        "geometry": args.geometry,
        "n_cells": n_total,
        "n_va": n_va,
        "n_non_va": n_non,
        "elapsed_s": elapsed,
        "seconds_per_cell": elapsed / n_total if n_total else None,
        "full_grid_expected_s": full_expected,
        "csv": str(csv_path),
        "heatmap": str(png),
        "wavelength_note": None if wave is None else wave.note,
        "tau_close_ms": TAU_CLOSE,
        "healthy_cv_band": "0.55-0.85 mm/ms (homogeneous sheet, same D)",
    }
    (args.out_dir / "phase_diagram_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    # Curated mirror for the public paper tree — only full annulus grids,
    # so smoke/fast runs cannot overwrite the 4×3 research CSV.
    if args.geometry == "annulus" and spec["mode"] == "full":
        papers_data = ROOT / "papers" / "data"
        papers_data.mkdir(parents=True, exist_ok=True)
        curated_csv = papers_data / "phase_diagram.csv"
        curated_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
        (papers_data / "phase_diagram_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        summary["curated_csv"] = str(curated_csv)
        print(f"Wrote curated {curated_csv}")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {csv_path}")

    if args.geometry == "annulus" and spec["mode"] == "fast" and not args.smoke:
        if n_va < 1 or n_non < 1:
            print(
                "ERROR: annulus fast grid must contain both VA and Non-VA; "
                "check wavelength vs path (docs/ASSUMPTIONS.md).",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
