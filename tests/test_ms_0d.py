"""Smoke tests for 0D Mitchell-Schaeffer."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from cardiac_ms.ms_0d import measure_apd, simulate_ms_0d


def test_simulate_produces_action_potential():
    t, u, meta = simulate_ms_0d(n_steps=3000, dt=0.1, seed=0)
    assert u.max() > 0.7
    assert meta["steps_per_s"] > 1000


def test_apd_in_physiological_range():
    t, u, _ = simulate_ms_0d(n_steps=5000, seed=1)
    apd = measure_apd(t, u)
    assert apd["apd_ms"] is not None
    assert 80 < apd["apd_ms"] < 400


def test_demo_cli_exits_zero(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "demo_ms_0d.py"),
            "--steps",
            "4000",
            "--out-dir",
            str(out),
            "--no-plot",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    summary = json.loads((out / "ms_0d_summary.json").read_text(encoding="utf-8"))
    assert summary["apd"]["apd_ms"] is not None
