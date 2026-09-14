#!/usr/bin/env python
"""Protocol helpers: DOX1 / DOX2 extras schedules on the verification annulus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.phenotypes import get_phenotype
from cardiac_ms.protocol_s1s2 import run_annulus_s1s2


def run_protocol(name: str, *, stimulus_mode: str = "current") -> dict:
    ph = get_phenotype(name)
    # CRITICAL: d_reduction=0.0 is valid (CONTROL); never use truthiness on float.
    d_red = float(ph.get("d_reduction", 0.0))
    r = run_annulus_s1s2(
        d_reduction=d_red,
        lam_ring=float(ph["params"]["lam"]),
        extra_cis_ms=tuple(ph["extra_cis_ms"]),
        tau_close_ring=float(ph["params"]["tau_close"]),
        stimulus_mode=stimulus_mode,
        params=dict(ph["params"]),
    )
    return {
        "phenotype": ph["name"],
        "label": r["label"],
        "VA_paper": r.get("VA_paper"),
        "VA_recurrence": r.get("VA_recurrence"),
        "VA_strict": r.get("VA_strict"),
        "VA_cycle": r.get("VA_cycle"),
        "activation_persists_ms": r["activation_persists_ms"],
        "n_extra_cycles": r["n_extra_cycles"],
        "n_probes_relapped": r.get("n_probes_relapped"),
        "d_reduction": d_red,
        "extra_cis_ms": list(ph["extra_cis_ms"]),
        "targets": ph["targets"],
        "notes": ph["notes"],
        "cv_matched": ph["cv_matched"],
        "apd_matched_0d": ph["apd_matched_0d"],
        "elapsed_s": r["elapsed_s"],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run DOX1/DOX2/CONTROL annulus protocol")
    p.add_argument("phenotype", choices=("CONTROL", "DOX1", "DOX2", "control", "dox1", "dox2"))
    p.add_argument("--stimulus-mode", choices=("current", "voltage_clamp"), default="current")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    summary = run_protocol(args.phenotype.upper(), stimulus_mode=args.stimulus_mode)
    text = json.dumps(summary, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
