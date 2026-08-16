#!/usr/bin/env python
"""Redraw paper/report figures with SciencePlots + Times New Roman.

Reads existing CSV/JSON under outputs/ (does not re-run heavy sims by default).
Writes PDF+PNG (300 dpi) to outputs/figures/ and papers/figures/.
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

import matplotlib.pyplot as plt
import numpy as np

from cardiac_ms.plotting import (
    apply_science_style,
    cjk_font_name,
    font_fallback_note,
    save_figure,
    text_fontproperties,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SciencePlots redraw of DOX-LBM_GPU figures")
    p.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "figures")
    p.add_argument("--paper-dir", type=Path, default=ROOT / "papers" / "figures")
    p.add_argument("--data-dir", type=Path, default=ROOT / "outputs")
    p.add_argument("--run-0d", action="store_true", help="Re-simulate 0D AP before plotting")
    p.add_argument("--run-mono2d", action="store_true", help="Re-run short mono2d snapshot")
    return p.parse_args()


def _dual_save(fig, stem: Path, paper_dir: Path) -> list[Path]:
    paths = save_figure(fig, stem, dpi=300, formats=("png", "pdf"))
    paper_dir.mkdir(parents=True, exist_ok=True)
    import shutil

    mirrored = []
    for p in paths:
        dest = paper_dir / p.name
        shutil.copy2(p, dest)
        mirrored.append(dest)
    plt.close(fig)
    return paths + mirrored


def plot_phase_diagram(data_dir: Path, out_dir: Path, paper_dir: Path) -> list[Path]:
    csv_path = data_dir / "phase_diagram.csv"
    if not csv_path.is_file():
        print(f"SKIP phase diagram: missing {csv_path}")
        return []

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if not rows:
        print("SKIP phase diagram: empty CSV")
        return []

    lams = sorted({float(r["lambda_fib"]) for r in rows})
    reds = sorted({float(r["d_reduction"]) for r in rows})
    grid = np.full((len(lams), len(reds)), np.nan)
    for r in rows:
        i = lams.index(float(r["lambda_fib"]))
        j = reds.index(float(r["d_reduction"]))
        grid[i, j] = float(r["va"])

    apply_science_style()
    # Avoid mathtext+CJK in one string (mathtext ignores CJK font fallback).
    fp = text_fontproperties(prefer_cjk=True)
    fig, ax = plt.subplots(figsize=(3.4, 2.8))
    im = ax.imshow(grid, origin="lower", vmin=0, vmax=1, cmap="coolwarm", aspect="auto")
    ax.set_xticks(range(len(reds)))
    ax.set_xticklabels([f"{100 * x:.0f}%" for x in reds], fontproperties=fp)
    ax.set_yticks(range(len(lams)))
    ax.set_yticklabels([f"{x:g}" for x in lams], fontproperties=fp)
    ax.set_xlabel("D_fib reduction / 纤维化扩散降幅", fontproperties=fp)
    ax.set_ylabel("lambda_fib / 兴奋性参数", fontproperties=fp)
    geom = rows[0].get("geometry", "annulus")
    ax.set_title(f"诱发性相图 Inducibility ({geom})", fontproperties=fp)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, ticks=[0, 1])
    cbar.ax.set_yticklabels(["Non-VA", "VA"], fontproperties=fp)
    # Annotate cells
    for i in range(len(lams)):
        for j in range(len(reds)):
            if np.isnan(grid[i, j]):
                continue
            label = "VA" if grid[i, j] >= 0.5 else "Non-VA"
            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                fontsize=7,
                color="k",
                fontproperties=fp,
            )
    fig.tight_layout()
    return _dual_save(fig, out_dir / "fig_phase_diagram", paper_dir)


def plot_ms_0d(data_dir: Path, out_dir: Path, paper_dir: Path, run: bool) -> list[Path]:
    from cardiac_ms.ms_0d import measure_apd, simulate_ms_0d

    summary_path = data_dir / "ms_0d_summary.json"
    if run or not summary_path.is_file():
        t, u, meta = simulate_ms_0d(n_steps=5000, dt=0.1, seed=42)
        apd = measure_apd(t, u)
        summary = {
            "apd": apd,
            "params": meta.get("params", {}),
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    else:
        # Always regenerate waveform for plotting (cheap)
        t, u, meta = simulate_ms_0d(n_steps=5000, dt=0.1, seed=42)
        apd = measure_apd(t, u)

    apply_science_style()
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    ax.plot(t, u, color="C0")
    apd_ms = float(apd["apd_ms"]) if isinstance(apd, dict) else float(apd)
    act = float(apd["activation_ms"]) if isinstance(apd, dict) else None
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel(r"$u$ (normalized)")
    title = f"0D Mitchell–Schaeffer (APD$_{{90}}$={apd_ms:.1f} ms)"
    ax.set_title(title)
    if act is not None:
        ax.axvline(act, color="0.5", ls="--", lw=0.7, label="activation")
        ax.axvline(act + apd_ms, color="0.5", ls=":", lw=0.7, label="APD end")
        ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    return _dual_save(fig, out_dir / "fig_ms_0d_ap", paper_dir)


def plot_validation_bars(data_dir: Path, out_dir: Path, paper_dir: Path) -> list[Path]:
    """Compact validation summary from existing JSON artefacts."""
    ms = data_dir / "ms_0d_summary.json"
    mono = data_dir / "mono2d_summary.json"
    phase = data_dir / "phase_diagram_summary.json"
    if not (ms.is_file() and phase.is_file()):
        print("SKIP validation bars: need ms_0d_summary.json + phase_diagram_summary.json")
        return []

    ms_j = json.loads(ms.read_text(encoding="utf-8"))
    phase_j = json.loads(phase.read_text(encoding="utf-8"))
    apd = float(ms_j["apd"]["apd_ms"])
    n_va = int(phase_j.get("n_va", 0))
    n_non = int(phase_j.get("n_non_va", 0))

    cv = None
    if mono.is_file():
        mono_j = json.loads(mono.read_text(encoding="utf-8"))
        # mono2d with fibrosis may report low CV; prefer validation module if present
        cv = mono_j.get("cv_mm_per_ms")

    # Prefer live validation CV if cheap
    try:
        from cardiac_ms.validation import validate_2d_cv_homogeneous

        cv_rep = validate_2d_cv_homogeneous()
        if isinstance(cv_rep, dict):
            for key in ("cv_mm_per_ms", "cv", "value"):
                if key in cv_rep and cv_rep[key] is not None:
                    cv = float(cv_rep[key])
                    break
            # nested common patterns
            if cv is None and "metrics" in cv_rep and isinstance(cv_rep["metrics"], dict):
                cv = float(cv_rep["metrics"].get("cv_mm_per_ms", cv or 0) or 0) or cv
    except Exception:
        pass

    apply_science_style()
    fig, axes = plt.subplots(1, 3, figsize=(5.5, 2.2))

    axes[0].bar([0], [apd], color="C0", width=0.6)
    axes[0].axhspan(248, 265, color="0.85", zorder=0)
    axes[0].set_xticks([])
    axes[0].set_ylabel("APD (ms)")
    axes[0].set_title("0D APD")
    axes[0].set_ylim(0, 320)

    if cv is not None:
        axes[1].bar([0], [cv], color="C1", width=0.6)
        axes[1].axhspan(0.55, 0.85, color="0.85", zorder=0)
        axes[1].axhline(0.70, color="k", ls="--", lw=0.7)
        axes[1].set_ylabel("CV (mm/ms)")
        axes[1].set_title("2D CV")
        axes[1].set_ylim(0, 1.0)
    else:
        axes[1].text(0.5, 0.5, "N/A", ha="center", va="center", transform=axes[1].transAxes)
        axes[1].set_title("2D CV")
    axes[1].set_xticks([])

    axes[2].bar([0, 1], [n_va, n_non], color=["C3", "C0"], width=0.6)
    axes[2].set_xticks([0, 1])
    axes[2].set_xticklabels(["VA", "Non-VA"])
    axes[2].set_ylabel("Count")
    axes[2].set_title("Phase (fast)")
    axes[2].set_ylim(0, max(n_va, n_non, 1) + 1)

    fig.tight_layout()
    return _dual_save(fig, out_dir / "fig_validation_summary", paper_dir)


def plot_diffusion_compare(data_dir: Path, out_dir: Path, paper_dir: Path) -> list[Path]:
    path = data_dir / "diffusion_operator_compare.json"
    if not path.is_file():
        print(f"SKIP diffusion compare: missing {path}")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    if not rows:
        return []

    cis = [r["ci_ms"] for r in rows]
    div_p = [r["div"]["activation_persists_ms"] for r in rows]
    lap_p = [r["laplace"]["activation_persists_ms"] for r in rows]

    apply_science_style()
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    x = np.arange(len(cis))
    w = 0.35
    ax.bar(x - w / 2, div_p, width=w, label=r"$\nabla\cdot(D\nabla u)$", color="C0")
    ax.bar(x + w / 2, lap_p, width=w, label=r"$D\nabla^2 u$", color="C1")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c:.0f}" for c in cis])
    ax.set_xlabel("CI (ms)")
    ax.set_ylabel("Persist (ms)")
    ax.set_title("Diffusion operator compare")
    ax.legend(loc="best", frameon=False)
    fig.tight_layout()
    return _dual_save(fig, out_dir / "fig_diffusion_compare", paper_dir)


def plot_mono2d_snapshot(out_dir: Path, paper_dir: Path, run: bool) -> list[Path]:
    """Short mono2d final-u heatmap (homogeneous, no fibrosis)."""
    from cardiac_ms.ms_2d import simulate_mono2d

    _ = run  # always regenerate a short snapshot (cheap vs full demo)
    t, u, h, meta = simulate_mono2d(
        nx=48,
        ny=48,
        n_steps=500,
        dt=0.1,
        dx=0.5,
        fibrosis=False,
        enforce_cfl=True,
        use_modified_ms=True,
        s2_window=(999999, 999999),
        snapshots=False,
    )
    _ = (t, h, meta)

    apply_science_style()
    fig, ax = plt.subplots(figsize=(2.8, 2.6))
    im = ax.imshow(u, origin="lower", cmap="viridis", vmin=0, vmax=1)
    ax.set_xlabel(r"$x$ index")
    ax.set_ylabel(r"$y$ index")
    ax.set_title("2D monodomain $u$")
    fig.colorbar(im, ax=ax, fraction=0.046, label=r"$u$")
    fig.tight_layout()
    return _dual_save(fig, out_dir / "fig_mono2d_u", paper_dir)


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.paper_dir.mkdir(parents=True, exist_ok=True)

    styles = apply_science_style()
    print(f"Applied styles: {styles}")
    note = font_fallback_note()
    cjk = cjk_font_name()
    font_lines = [
        f"Times New Roman / CJK stack applied via cardiac_ms.plotting",
        f"CJK font: {cjk or 'NONE'}",
        f"Note: {note or 'OK'}",
    ]
    print("FONT: " + "; ".join(font_lines))
    (args.out_dir / "FONT_NOTE.txt").write_text("\n".join(font_lines) + "\n", encoding="utf-8")
    (args.paper_dir / "FONT_NOTE.txt").write_text("\n".join(font_lines) + "\n", encoding="utf-8")

    all_paths: list[Path] = []
    all_paths += plot_phase_diagram(args.data_dir, args.out_dir, args.paper_dir)
    all_paths += plot_ms_0d(args.data_dir, args.out_dir, args.paper_dir, args.run_0d)
    all_paths += plot_validation_bars(args.data_dir, args.out_dir, args.paper_dir)
    all_paths += plot_diffusion_compare(args.data_dir, args.out_dir, args.paper_dir)
    try:
        all_paths += plot_mono2d_snapshot(args.out_dir, args.paper_dir, args.run_mono2d)
    except Exception as exc:
        print(f"SKIP mono2d figure: {exc}")

    manifest = {
        "styles": styles,
        "font_note": note,
        "cjk_font": cjk,
        "files": [str(p) for p in all_paths],
        "n_files": len(all_paths),
    }
    (args.out_dir / "figure_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0 if all_paths else 1


if __name__ == "__main__":
    raise SystemExit(main())
