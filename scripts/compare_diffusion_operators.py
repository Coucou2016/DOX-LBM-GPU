#!/usr/bin/env python
"""
P2 scaffold: same S1–S2 on variable-D tissue with div(D∇u) vs D⊙∇²u.

Reports whether the VA / persist classification changes. Does not download
external datasets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.constants import D_HEALTHY_MM2_PER_MS, LAMBDA_HEALTHY
from cardiac_ms.protocol_s1s2 import run_s1s2
from cardiac_ms.tissue_classes import disk_fibrosis_three_class


def one_run(mode: str, ci_ms: float, tissue) -> dict:
    r = run_s1s2(
        nx=40,
        ny=40,
        dx=0.5,
        n_s1=1,
        extra_cis_ms=(ci_ms,),
        observe_ms=500.0,
        tissue=tissue,
        s2_cross_field=True,
        diffusion_mode=mode,
        dt=0.1,
    )
    return {
        "diffusion_mode": mode,
        "ci_ms": ci_ms,
        "label": r["label"],
        "activation_persists_ms": r["activation_persists_ms"],
        "n_extra_cycles": r["n_extra_cycles"],
        "elapsed_s": r["elapsed_s"],
        "cfl_r": r["cfl_r"],
    }


def main() -> int:
    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    tissue = disk_fibrosis_three_class(
        40,
        40,
        border_width=2,
        D_healthy=D_HEALTHY_MM2_PER_MS,
        d_reduction_dense=0.90,
        lam_healthy=LAMBDA_HEALTHY,
        lam_dense=0.2,
    )
    cis = (200.0, 240.0, 280.0)
    rows = []
    for ci in cis:
        a = one_run("div", ci, tissue)
        b = one_run("laplace", ci, tissue)
        rows.append(
            {
                "ci_ms": ci,
                "div": a,
                "laplace": b,
                "label_changed": a["label"] != b["label"],
                "persist_delta_ms": a["activation_persists_ms"] - b["activation_persists_ms"],
            }
        )
        print(
            f"CI={ci:.0f}  div={a['label']} persist={a['activation_persists_ms']:.1f}  "
            f"laplace={b['label']} persist={b['activation_persists_ms']:.1f}  "
            f"changed={a['label'] != b['label']}"
        )

    n_changed = sum(1 for r in rows if r["label_changed"])
    summary = {
        "n_ci": len(cis),
        "n_label_changed": n_changed,
        "critical_ci_changed": n_changed > 0,
        "rows": rows,
        "note": (
            "div(D∇u) is the conservative operator; D*laplace is the common shortcut "
            "and is inconsistent when D varies. A label change means the shortcut "
            "would mis-estimate inducibility on this 2D prototype."
        ),
    }
    path = out_dir / "diffusion_operator_compare.json"
    path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {path}")
    print(f"critical_ci_changed={summary['critical_ci_changed']} ({n_changed}/{len(cis)} CIs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
