#!/usr/bin/env python
"""Optional capture-threshold scan: STIM_CURRENT vs STIM_VOLTAGE on a small sheet.

Sweeps stimulus amplitude under ``stimulus_mode=current`` (and optionally
voltage_clamp) on a 1D cable or tiny 2D sheet; reports the lowest amplitude
that captures an AP (u_max ≥ 0.5). Does not invent physiology — diagnostic only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from cardiac_ms.constants import (
    STIM_CURRENT_AMP,
    STIM_DURATION_MS,
    STIM_VOLTAGE_CLAMP_U,
)
from cardiac_ms.ms_2d import simulate_mono2d
from cardiac_ms.protocol_s1s2 import Stimulus


def scan_capture(
    *,
    amps: list[float],
    stimulus_mode: str = "current",
    nx: int = 32,
    ny: int = 8,
    dx: float = 0.5,
    dt: float = 0.1,
) -> list[dict]:
    rows = []
    region = (slice(0, ny), slice(0, max(2, nx // 8)))
    for amp in amps:
        stim = [
            Stimulus(
                0.0,
                STIM_DURATION_MS,
                region,
                stim_u=STIM_VOLTAGE_CLAMP_U if stimulus_mode == "voltage_clamp" else amp,
                stim_amp=amp,
            )
        ]
        _, u, _, meta = simulate_mono2d(
            nx=nx,
            ny=ny,
            dx=dx,
            dt=dt,
            t_end_ms=40.0,
            stimuli=stim,
            stimulus_mode=stimulus_mode,
            track_reentry=False,
            snapshots=False,
        )
        u_max = float(meta.get("u_peak") or u.max())
        rows.append(
            {
                "stimulus_mode": stimulus_mode,
                "amp": float(amp),
                "u_max": u_max,
                "captured": bool(u_max >= 0.5),
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("current", "voltage_clamp", "both"), default="both")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "capture_threshold_scan.json")
    args = ap.parse_args()
    amps = [0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
    report: dict = {
        "STIM_VOLTAGE_CLAMP_U": STIM_VOLTAGE_CLAMP_U,
        "STIM_CURRENT_AMP": STIM_CURRENT_AMP,
        "units": {
            "STIM_VOLTAGE_CLAMP_U": "dimensionless u clamp target",
            "STIM_CURRENT_AMP": "J_stim amplitude added during stim window",
        },
        "induction_rule": "use ~1.5 * Jc for induction once Jc is measured",
        "amps": amps,
        "scans": {},
    }
    modes = ("current", "voltage_clamp") if args.mode == "both" else (args.mode,)
    for mode in modes:
        rows = scan_capture(amps=amps, stimulus_mode=mode)
        captured = [r["amp"] for r in rows if r["captured"]]
        jc = float(min(captured)) if captured else None
        report["scans"][mode] = {
            "rows": rows,
            "threshold_amp_Jc": jc,
            "induction_amp_1p5_Jc": (1.5 * jc) if jc is not None else None,
        }
        print(
            f"{mode}: Jc={jc}  induction≈{report['scans'][mode]['induction_amp_1p5_Jc']}"
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
