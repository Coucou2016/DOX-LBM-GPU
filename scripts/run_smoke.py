#!/usr/bin/env python
"""Run all smoke checks; exit 0 on success."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTEST_ENV = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}


def run(cmd: list[str], label: str) -> float:
    print(f"\n=== {label} ===")
    print(" ".join(cmd))
    t0 = time.perf_counter()
    env = PYTEST_ENV if "pytest" in cmd else None
    proc = subprocess.run(cmd, cwd=ROOT, timeout=300, env=env)
    elapsed = time.perf_counter() - t0
    if proc.returncode != 0:
        raise SystemExit(f"{label} failed with code {proc.returncode}")
    print(f"OK ({elapsed:.2f}s)")
    return elapsed


def main() -> int:
    py = sys.executable
    timings: dict[str, float] = {}

    timings["ms_0d"] = run(
        [py, "demo_ms_0d.py", "--steps", "3000", "--no-plot"],
        "0D MS demo",
    )
    timings["mono2d"] = run(
        [
            py,
            "demo_mono2d.py",
            "--steps",
            "2000",
            "--nx",
            "48",
            "--ny",
            "48",
            "--dx",
            "0.5",
        ],
        "2D monodomain",
    )
    timings["synthetic"] = run(
        [py, "scripts/generate_synthetic_data.py"],
        "synthetic data",
    )
    timings["validation"] = run(
        [py, "-m", "cardiac_ms.validation"],
        "reference validation",
    )
    timings["pytest"] = run(
        [py, "-m", "pytest", "tests/", "-q"],
        "pytest",
    )

    log = ROOT / "outputs" / "smoke_timings.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}: {v:.3f}s" for k, v in timings.items()]
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {log}")
    print("All smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
