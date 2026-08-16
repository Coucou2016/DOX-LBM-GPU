"""Publication plotting helpers: SciencePlots + Times New Roman (Windows).

Prefer ``science`` + ``no-latex`` so figures render without a TeX install.
Font sizes target single-column Nature-ish panels (~89 mm).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# SciencePlots 2.x registers styles on import
try:
    import scienceplots  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "SciencePlots is required. Install with: pip install SciencePlots"
    ) from exc

# Paper sizes (pt): labels 9–10, ticks 8, title 10–11, legend 8
_PAPER_RC = {
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.titlesize": 11,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    # Allow minus signs / CJK without missing-glyph boxes when possible
    "axes.unicode_minus": False,
}

# Prefer TrueType (.ttf) faces for Matplotlib CJK labels; .ttc (YaHei/SimSun)
# often falls back to a glyph-less "default" font on Windows.
_CJK_CANDIDATES = (
    "SimHei",
    "Microsoft YaHei",
    "SimSun",
    "Noto Sans CJK SC",
    "Noto Serif CJK SC",
    "Source Han Sans SC",
    "WenQuanYi Micro Hei",
)

_FONT_NOTE: str | None = None
_CJK_FONT: str | None = None


def _has_font(name: str) -> bool:
    return any(f.name == name for f in fm.fontManager.ttflist)


def _first_available(names: tuple[str, ...]) -> str | None:
    for name in names:
        if _has_font(name):
            return name
    return None


def font_fallback_note() -> str | None:
    """Return a short note if Times New Roman / CJK fonts were unavailable."""
    return _FONT_NOTE


def cjk_font_name() -> str | None:
    """Name of the selected CJK-capable font, if any."""
    return _CJK_FONT


def text_fontproperties(*, prefer_cjk: bool = True):
    """FontProperties for mixed-script labels.

    Prefer a ``.ttf`` CJK face (e.g. SimHei). Binding ``.ttc`` collections such as
    Microsoft YaHei via ``fname`` can silently fall back to Matplotlib's
    glyph-less ``default`` font on Windows.
    """
    from matplotlib.font_manager import FontProperties

    if prefer_cjk:
        # Prefer .ttf paths first
        ttf_hit = None
        ttc_hit = None
        for name in _CJK_CANDIDATES:
            for entry in fm.fontManager.ttflist:
                if entry.name != name or not entry.fname:
                    continue
                low = entry.fname.lower()
                if low.endswith(".ttf") and ttf_hit is None:
                    ttf_hit = entry.fname
                elif low.endswith(".ttc") and ttc_hit is None:
                    ttc_hit = entry.fname
        if ttf_hit:
            return FontProperties(fname=ttf_hit)
        if ttc_hit:
            return FontProperties(fname=ttc_hit)
        cjk = _CJK_FONT or _first_available(_CJK_CANDIDATES)
        if cjk:
            return FontProperties(family=cjk)
    if _has_font("Times New Roman"):
        return FontProperties(family="Times New Roman")
    return FontProperties(family="DejaVu Serif")


def apply_science_style(*, prefer_latex: bool = False) -> list[str]:
    """Apply SciencePlots style with TNR (English) + CJK-capable font stack.

    Returns the style list that was successfully applied.
    """
    global _FONT_NOTE, _CJK_FONT
    styles: list[str] = ["science"]
    if prefer_latex:
        styles.append("ieee")  # latex-friendly if available
    else:
        styles.append("no-latex")

    applied: list[str] = []
    try:
        plt.style.use(styles)
        applied = list(styles)
    except OSError:
        # Minimal fallback if SciencePlots styles are missing
        try:
            plt.style.use(["science", "no-latex"])
            applied = ["science", "no-latex"]
        except OSError:
            mpl.rcParams.update(_PAPER_RC)
            applied = []

    mpl.rcParams.update(_PAPER_RC)

    notes: list[str] = []
    has_tnr = _has_font("Times New Roman")
    # Prefer a .ttf CJK face for rc reporting / fallbacks
    cjk = None
    for name in _CJK_CANDIDATES:
        for entry in fm.fontManager.ttflist:
            if entry.name == name and entry.fname and entry.fname.lower().endswith(".ttf"):
                cjk = name
                break
        if cjk:
            break
    if cjk is None:
        cjk = _first_available(_CJK_CANDIDATES)
    _CJK_FONT = cjk

    # Mixed Latin + CJK: put TNR and a CJK face in the *same* family list.
    # On Windows, a single-name family (e.g. only "Times New Roman") will not
    # substitute missing CJK glyphs; a multi-name family list enables fallback.
    latin = "Times New Roman" if has_tnr else "DejaVu Serif"
    if not has_tnr:
        notes.append("Times New Roman not found; Latin uses DejaVu Serif.")
    if not cjk:
        notes.append(
            "No CJK font found (tried YaHei/SimSun/Noto); Chinese labels may fail."
        )

    family_list: list[str] = [latin]
    if cjk:
        family_list.append(cjk)
    family_list.append("DejaVu Serif")

    # Prefer sans-serif family slot: SciencePlots + Win32 glyph fallback is more
    # reliable there for mixed scripts; keep serif list identical for consistency.
    mpl.rcParams["font.family"] = family_list
    mpl.rcParams["font.serif"] = family_list
    mpl.rcParams["font.sans-serif"] = family_list
    mpl.rcParams["mathtext.fontset"] = "stix"
    _FONT_NOTE = " ".join(notes) if notes else None
    return applied


def save_figure(
    fig: mpl.figure.Figure,
    stem: Path | str,
    *,
    dpi: int = 300,
    formats: Sequence[str] = ("png", "pdf"),
) -> list[Path]:
    """Save figure as PNG+PDF (and optional extras) next to *stem*."""
    stem_path = Path(stem)
    stem_path.parent.mkdir(parents=True, exist_ok=True)
    # strip extension if caller passed one
    if stem_path.suffix.lower() in {".png", ".pdf", ".svg", ".tiff"}:
        stem_path = stem_path.with_suffix("")
    out: list[Path] = []
    for ext in formats:
        path = stem_path.with_suffix(f".{ext}")
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        out.append(path)
    return out


def mirror_copies(paths: Iterable[Path], *dest_dirs: Path) -> list[Path]:
    """Copy saved figures into additional directories (e.g. papers/figures)."""
    import shutil

    mirrored: list[Path] = []
    for dest in dest_dirs:
        dest.mkdir(parents=True, exist_ok=True)
        for src in paths:
            target = dest / src.name
            shutil.copy2(src, target)
            mirrored.append(target)
    return mirrored
