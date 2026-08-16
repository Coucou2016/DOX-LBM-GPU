"""2D monodomain + MS prototype (CPU). Saves snapshots to outputs/."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from cardiac_ms.ms_2d import simulate_mono2d


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="2D monodomain MS prototype")
    p.add_argument("--nx", type=int, default=64)
    p.add_argument("--ny", type=int, default=64)
    p.add_argument("--steps", type=int, default=2500)
    p.add_argument("--dt", type=float, default=0.1, help="Time step (ms); CFL-clamped if too large")
    p.add_argument("--dx", type=float, default=0.5, help="Grid spacing (mm)")
    p.add_argument("--no-fibrosis", action="store_true")
    p.add_argument("--no-s2", action="store_true", help="Disable S2 stimulus")
    p.add_argument("--no-cfl", action="store_true", help="Skip CFL clamp on dt")
    p.add_argument("--out-dir", type=Path, default=Path("outputs"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    s2_coupling = 99999.0 if args.no_s2 else 180.0
    s2_window = None if args.no_s2 else None

    t, u, h, meta = simulate_mono2d(
        nx=args.nx,
        ny=args.ny,
        n_steps=args.steps,
        dt=args.dt,
        dx=args.dx,
        fibrosis=not args.no_fibrosis,
        enforce_cfl=not args.no_cfl,
        s2_coupling_ms=s2_coupling,
        s2_window=(999999, 999999) if args.no_s2 else s2_window,
    )

    summary = {
        "shape": [args.ny, args.nx],
        "u_max": float(u.max()),
        "u_mean": float(u.mean()),
        "dt_ms": meta["dt"],
        "dx_mm": meta["dx"],
        "cfl_r": meta["cfl_r"],
        "cv_mm_per_ms": meta.get("cv_mm_per_ms"),
        "u_peak": meta.get("u_peak"),
        "D_min": meta.get("D_min"),
        "D_max": meta.get("D_max"),
        "lam_min": meta.get("lam_min"),
        "lam_max": meta.get("lam_max"),
        "use_modified_ms": meta.get("use_modified_ms"),
        "timing_ms": meta["elapsed_s"] * 1000,
        "ms_per_step": meta["ms_per_step"],
        "fibrosis": meta["fibrosis"],
    }
    path = out_dir / "mono2d_summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

    np.savez_compressed(out_dir / "mono2d_final.npz", u=u, h=h, t_ms=t)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    im0 = axes[0].imshow(u, origin="lower", cmap="viridis", vmin=0, vmax=1)
    axes[0].set_title("u final")
    plt.colorbar(im0, ax=axes[0], fraction=0.046)
    im1 = axes[1].imshow(h, origin="lower", cmap="plasma", vmin=0, vmax=1)
    axes[1].set_title("h final")
    plt.colorbar(im1, ax=axes[1], fraction=0.046)
    plt.tight_layout()
    png = out_dir / "mono2d_final.png"
    plt.savefig(png, dpi=120)
    print(f"Wrote {png}")

    peak = float(meta.get("u_peak") or u.max())
    if peak < 0.15:
        print("WARNING: little activation; check pacing windows.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
