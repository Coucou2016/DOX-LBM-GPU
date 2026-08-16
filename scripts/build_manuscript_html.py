#!/usr/bin/env python
"""Build self-contained papers/manuscript.html from manuscript_draft.md.

Embeds papers/figures/*.png as base64 data URIs. Inline CSS only (no CDN).
"""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "papers" / "manuscript_draft.md"
OUT = ROOT / "papers" / "manuscript.html"
FIG_DIR = ROOT / "papers" / "figures"


def png_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def md_to_html_body(text: str) -> str:
    """Minimal markdown subset → HTML (headings, lists, tables, images, code, bold)."""
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_code = False
    code_buf: list[str] = []
    in_ul = False
    in_ol = False
    in_table = False
    table_rows: list[list[str]] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not table_rows:
            return
        header = table_rows[0]
        body = table_rows[1:]
        # skip markdown separator row
        if body and all(re.match(r"^:?-+:?$", c.strip()) for c in body[0]):
            body = body[1:]
        thead = "".join(f"<th>{inline(c)}</th>" for c in header)
        trs = []
        for row in body:
            trs.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
        out.append(
            '<table class="data"><thead><tr>'
            + thead
            + "</tr></thead><tbody>"
            + "".join(trs)
            + "</tbody></table>"
        )
        table_rows = []
        in_table = False

    def inline(s: str) -> str:
        # images ![alt](path)
        def img_repl(m: re.Match[str]) -> str:
            alt, src = m.group(1), m.group(2)
            # resolve relative to papers/
            p = (ROOT / "papers" / src).resolve()
            if not p.is_file():
                p2 = FIG_DIR / Path(src).name
                p = p2 if p2.is_file() else p
            if p.is_file() and p.suffix.lower() == ".png":
                return (
                    f'<img class="fig" src="{png_uri(p)}" alt="{html.escape(alt)}" />'
                )
            return f'<p class="warn">[missing figure: {html.escape(src)}]</p>'

        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img_repl, s)
        # links
        s = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda m: f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>',
            s,
        )
        # inline code
        s = re.sub(r"`([^`]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", s)
        # bold / italic
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
        # simple latex-ish keep as-is escaped then unescape common
        return s

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf = []
                in_code = False
            else:
                close_lists()
                flush_table()
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if "|" in line and line.strip().startswith("|"):
            close_lists()
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table_rows.append(cells)
            in_table = True
            i += 1
            continue
        elif in_table:
            flush_table()

        if line.startswith("# "):
            close_lists()
            out.append(f"<h1>{inline(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            close_lists()
            out.append(f"<h2>{inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            close_lists()
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("> "):
            close_lists()
            out.append(f'<p class="note">{inline(line[2:].strip())}</p>')
        elif re.match(r"^- ", line):
            if not in_ul:
                close_lists()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:].strip())}</li>")
        elif re.match(r"^\d+\. ", line):
            if not in_ol:
                close_lists()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(re.sub(r'^\\d+\\. ', '', line).strip())}</li>")
        elif line.strip() == "---":
            close_lists()
            out.append("<hr />")
        elif line.strip() == "":
            close_lists()
        else:
            close_lists()
            out.append(f"<p>{inline(line.strip())}</p>")
        i += 1

    close_lists()
    flush_table()
    return "\n".join(out)


CSS = """
:root { --fg:#1a1a1a; --muted:#444; --accent:#1f4e79; --line:#c8c8c8; --bg:#fbfbf8; }
* { box-sizing: border-box; }
body {
  margin: 0; color: var(--fg);
  background: linear-gradient(180deg, #eef2f6 0%, var(--bg) 240px);
  font-family: "Times New Roman", "SimSun", "Microsoft YaHei", serif;
  line-height: 1.65; font-size: 16px;
}
.wrap { max-width: 900px; margin: 0 auto; padding: 28px 22px 64px; }
h1 { color: var(--accent); font-size: 1.45rem; line-height: 1.35; }
h2 { color: var(--accent); border-bottom: 1px solid var(--line); padding-bottom: 6px; margin-top: 1.6em; }
h3 { margin-top: 1.2em; }
.note { background: #f5f7fa; border-left: 3px solid var(--accent); padding: 10px 14px; color: var(--muted); }
img.fig { display:block; width:100%; max-width:640px; margin: 12px auto; border:1px solid #ddd; }
table.data { width:100%; border-collapse: collapse; font-size: 0.85rem; display:block; overflow-x:auto; }
table.data th, table.data td { border:1px solid var(--line); padding:5px 7px; }
table.data th { background:#e8eef5; }
code { background:#f0f0f0; padding:1px 4px; font-size:0.92em; }
pre { background:#f4f4f4; padding:12px; overflow-x:auto; }
.warn { color:#8a1f1f; }
footer { color:var(--muted); font-size:0.9rem; text-align:center; margin-top:36px; }
"""


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    body = md_to_html_body(md)
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>DOX-LBM_GPU manuscript draft</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
{body}
<footer>
Self-contained HTML from <code>papers/manuscript_draft.md</code> via
<code>scripts/build_manuscript_html.py</code>. Figures are base64 PNG; no CDN.
</footer>
</div>
</body>
</html>
"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
