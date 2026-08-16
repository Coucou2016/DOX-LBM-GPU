"""Phase-diagram CLI smoke on a tiny annulus grid."""

import subprocess
import sys
from pathlib import Path


def test_phase_diagram_smoke_tiny_grid(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "run_phase_diagram.py"),
            "--smoke",
            "--geometry",
            "annulus",
            "--out-dir",
            str(tmp_path),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    csv = tmp_path / "phase_diagram.csv"
    assert csv.exists()
    text = csv.read_text(encoding="utf-8")
    assert "annulus" in text
    assert "label" in text
