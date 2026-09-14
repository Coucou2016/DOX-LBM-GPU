#!/usr/bin/env python
"""
Cross-check λ-MS ionic RHS vs javilva/doxorubicin_fibrosis_model (PyTorch formulas).

Clone once (optional):
  git clone --depth 1 https://github.com/javilva/doxorubicin_fibrosis_model.git _ext_dox_fibrosis

Reports max |Δdu/dt| and |Δdh/dt| for λ in {0.01, 0.1, 0.2, 0.3}.
Does not invent physiology — only algebraic agreement of published cell-model RHS.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.ms_modified import get_modified_parameters, ionic_rhs_modified

EXT = ROOT / "_ext_dox_fibrosis"
LAMBDAS = (0.01, 0.1, 0.2, 0.3)


def javilva_rhs_numpy(u, h, *, lam, tau_in, tau_out, tau_open, tau_close, u_gate, u_max):
    """Same algebra as javilva model/mitchell_schaeffer.py (NumPy)."""
    j_in = h * u * (u - lam) * (u_max - u) / tau_in
    j_out = -u / tau_out
    du = j_in + j_out
    dh = np.where(u < u_gate, (1.0 - h) / tau_open, -h / tau_close)
    return du, dh


def main() -> int:
    rng = np.random.default_rng(0)
    u = rng.random(2000)
    h = rng.random(2000)
    # Mix resting / excited samples
    u[:200] = rng.uniform(0.0, 0.2, 200)
    u[200:400] = rng.uniform(0.5, 1.0, 200)

    note = None
    if EXT.is_dir() and (EXT / "model" / "mitchell_schaeffer.py").is_file():
        # Relative path only — never embed machine-local absolute roots in JSON.
        note = (
            "Found clone at _ext_dox_fibrosis "
            "(solver proprietary per their README)."
        )
        # Prefer importing their module if torch available
        sys.path.insert(0, str(EXT))
        try:
            import torch
            from model.mitchell_schaeffer import DEFAULT_PARAMETERS, dh_dt, dv_dt

            use_torch = True
        except Exception as exc:  # noqa: BLE001
            use_torch = False
            note += f" Torch import failed ({exc}); using NumPy twin of their formulas."
    else:
        use_torch = False
        note = (
            "Clone missing: compared against NumPy twin of javilva formulas "
            "(https://github.com/javilva/doxorubicin_fibrosis_model)."
        )

    rows = []
    # Their DEFAULT uses tau_close=189; we also check with our tau_close=150.
    for tau_close in (150.0, 189.0):
        for lam in LAMBDAS:
            p = get_modified_parameters(lam=lam)
            p["tau_close"] = tau_close
            rhs_ours, dh_ours = ionic_rhs_modified(u, h, p, lam=lam)
            rhs_ours = np.asarray(rhs_ours, dtype=np.float64)
            dh_ours = np.asarray(dh_ours, dtype=np.float64)

            if use_torch:
                vt = torch.tensor(u, dtype=torch.float64)
                ht = torch.tensor(h, dtype=torch.float64)
                du_t = dv_dt(
                    vt,
                    ht,
                    tau_in=p["tau_in"],
                    tau_out=p["tau_out"],
                    v_max=p["u_max"],
                    lambda_=lam,
                )
                dh_t = torch.empty_like(ht)
                dh_dt(
                    dh_t,
                    vt,
                    ht,
                    tau_open=p["tau_open"],
                    tau_close=tau_close,
                    v_gate=p["u_gate"],
                )
                rhs_ref = du_t.detach().cpu().numpy()
                dh_ref = dh_t.detach().cpu().numpy()
                backend = "torch_javilva"
            else:
                rhs_ref, dh_ref = javilva_rhs_numpy(
                    u,
                    h,
                    lam=lam,
                    tau_in=p["tau_in"],
                    tau_out=p["tau_out"],
                    tau_open=p["tau_open"],
                    tau_close=tau_close,
                    u_gate=p["u_gate"],
                    u_max=p["u_max"],
                )
                backend = "numpy_javilva_twin"

            row = {
                "lam": lam,
                "tau_close": tau_close,
                "backend": backend,
                "max_abs_du": float(np.max(np.abs(rhs_ours - rhs_ref))),
                "max_abs_dh": float(np.max(np.abs(dh_ours - dh_ref))),
            }
            rows.append(row)
            print(
                f"lam={lam} tau_close={tau_close} [{backend}] "
                f"max|Δdu|={row['max_abs_du']:.3e} max|Δdh|={row['max_abs_dh']:.3e}"
            )

    out = {
        "note": note,
        "javilva_default_tau_close": 189.0,
        "our_default_tau_close": 150.0,
        "rows": rows,
        "all_ok": all(r["max_abs_du"] < 1e-12 and r["max_abs_dh"] < 1e-12 for r in rows),
    }
    out_path = ROOT / "outputs" / "javilva_rhs_crosscheck.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    data_path = ROOT / "data" / "javilva_rhs_crosscheck.json"
    data_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"all_ok": out["all_ok"], "wrote": str(out_path)}, indent=2))
    print(note)
    return 0 if out["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
