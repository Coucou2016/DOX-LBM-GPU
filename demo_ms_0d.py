"""0D Mitchell-Schaeffer demo with CLI, APD, and parameter sweep."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cardiac_ms.ms_0d import measure_apd, parameter_sweep_tau_out, simulate_ms_0d


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mitchell-Schaeffer 0D demo")
    p.add_argument("--steps", type=int, default=5000)
    p.add_argument("--dt", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", type=Path, default=Path("outputs"))
    p.add_argument("--sweep", action="store_true", help="Run tau_out parameter sweep")
    p.add_argument("--no-plot", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    t, u, meta = simulate_ms_0d(
        n_steps=args.steps,
        dt=args.dt,
        seed=args.seed,
    )
    apd = measure_apd(t, u)

    summary = {
        "apd": apd,
        "timing": {
            "elapsed_ms": meta["elapsed_s"] * 1000,
            "steps_per_s": meta["steps_per_s"],
        },
        "params": meta["params"],
    }
    summary_path = out_dir / "ms_0d_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

    if args.sweep:
        sweep = parameter_sweep_tau_out(n_steps=min(args.steps, 4000), dt=args.dt, seed=args.seed)
        sweep_path = out_dir / "ms_0d_sweep.json"
        sweep_path.write_text(
            json.dumps(
                [
                    {
                        "tau_out": r["tau_out"],
                        "apd_ms": r.get("apd_ms"),
                        "peak_u": r.get("peak_u"),
                    }
                    for r in sweep
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Wrote sweep to {sweep_path}")

    if not args.no_plot:
        fig_path = out_dir / "ms_0d_action_potential.png"
        plt.figure(figsize=(8, 3))
        plt.plot(t, u)
        plt.xlabel("time (ms)")
        plt.ylabel("u (normalized)")
        plt.title("Mitchell-Schaeffer 0D")
        plt.tight_layout()
        plt.savefig(fig_path, dpi=120)
        print(f"Wrote {fig_path}")

    duration_ms = args.steps * args.dt
    if u.max() < 0.5:
        print("ERROR: no action potential detected.", file=sys.stderr)
        return 1
    if apd.get("apd_ms") is None and duration_ms < 350:
        print(
            f"WARNING: simulation ends at {duration_ms:.0f} ms before repolarization; "
            "increase --steps for APD.",
            file=sys.stderr,
        )
    elif apd.get("apd_ms") is not None and apd["apd_ms"] < 10:
        print("ERROR: APD unrealistically short.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
