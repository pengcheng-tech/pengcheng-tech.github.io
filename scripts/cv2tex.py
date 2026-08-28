#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cv2tex.py — Generate a LaTeX CV and compile it to PDF from _data/cv.json
(+ publications.bib).

Data flow (single source):
  _data/cv.json            — biography, experience, education, projects,
                             awards, service, supervision, activities,
                             publications (with `bib_key` where applicable)
  publications.bib         — authoritative metadata (DOI, pages) for papers
                             referenced by `bib_key`
  _data/patents.yml        — optional; granted patents section (LOCAL file,
                             gitignored) only when --patents is given
        |
        v
  LaTeX -> pdflatex -> <out>.pdf

Usage:
  python3 scripts/cv2tex.py --dry-run            # write the .tex only, no compile
  python3 scripts/cv2tex.py                      # compile to files/CV_Peng_Cheng.pdf
  python3 scripts/cv2tex.py --out /tmp/cv.pdf
  python3 scripts/cv2tex.py --patents            # include Granted Patents (local file)
  python3 scripts/cv2tex.py --keep-tex           # keep the generated .tex next to the PDF
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CV = ROOT / "_data" / "cv.json"
DEFAULT_BIB = ROOT / "publications.bib"
DEFAULT_OUT = ROOT / "files" / "CV_Peng_Cheng.pdf"
PATENTS_YML = ROOT / "_data" / "patents.yml"

TEX_PREAMBLE = r"""\documentclass[10pt,a4paper]{article}
\usepackage[margin=1.6cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{textcomp}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\titleformat{\section}{\large\bfseries}{}{0em}{}[\vspace{-4pt}\rule{\textwidth}{0.6pt}]
\titlespacing*{\section}{0pt}{10pt}{6pt}
\newcommand{\cvname}[1]{{\LARGE\bfseries #1}}
\newcommand{\cvcontact}[1]{{\small #1}}
\begin{document}
"""

TEX_END = r"""\end{document}
"""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def latex_escape(text):
    """Escape text for LaTeX, mapping common unicode to macros."""
    text = str(text)
    mapping = {
        "\\": r"\textbackslash{}",
        "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&", "#": r"\#",
        "%": r"\%", "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "’": "'", "‘": "`", "“": "``", "”": "''",
        "–": "--", "—": "---", "£": r"\pounds{}", "€": r"\texteuro{}",
        "•": r"\textbullet{}",
        "ã": r"\~a", "á": r"\'a", "é": r"\'e", "í": r"\'i", "ó": r"\'o", "ú": r"\'u",
        "ç": r"\c{c}", "ñ": r"\~n", "ü": r"\"u", "ö": r"\"o", "ä": r"\"a",
    }
    out = []
    for ch in text:
        out.append(mapping.get(ch, ch))
    return "".join(out)


def parse_bib(path):
    """Minimal BibTeX parser: key -> fields (reused from sync_orcid style)."""
    text = Path(path).read_text(encoding="utf-8")
    entries = {}
    i, n = 0, len(text)
    while i < n:
        m = re.compile(r"@\s*([A-Za-z]+)\s*\{").search(text, i)
        if not m:
            break
        j = m.end()
        k = text.find(",", j)
        if k < 0:
            break
        key = text[j:k].strip()
        fields = {}
        p = k + 1
        while p < n:
            while p < n and (text[p].isspace() or text[p] == ","):
                p += 1
            if p >= n or text[p] == "}":
                break
            fm = re.compile(r"([A-Za-z0-9_\-]+)\s*=").match(text, p)
            if not fm:
                break
            name = fm.group(1).lower()
            p = fm.end()
            while p < n and text[p].isspace():
                p += 1
            if p < n and text[p] == "{":
                depth = 0
                start = p
                while p < n:
                    if text[p] == "{":
                        depth += 1
                    elif text[p] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    p += 1
                val = text[start + 1:p]
                p += 1
            else:
                m2 = re.compile(r"[^,\s}]+").match(text, p)
                val = m2.group(0) if m2 else ""
                p = m2.end() if m2 else p
            fields[name] = val.strip()
        entries[key] = fields
        depth = 0
        while j < n:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        i = j
    return entries


def bold_name(authors):
    """Bold the author's own name in an author list."""
    names = [a.strip() for a in authors if a.strip()]
    if not names:
        return ""
    out = []
    for name in names:
        if re.fullmatch(r"Peng\s+Cheng", name):
            out.append(r"\textbf{" + latex_escape(name) + "}")
        else:
            out.append(latex_escape(name))
    return ", ".join(out)


def fmt_pub(pub, bib):
    """Format one publication entry as a LaTeX line."""
    key = pub.get("bib_key")
    f = bib.get(key) or {}
    authors = pub.get("authors") or []
    if f.get("author"):
        authors = [a.strip() for a in f["author"].split(" and ")]
    year = pub.get("year") or f.get("year") or ""
    title = pub.get("name") or f.get("title") or ""
    venue = pub.get("publisher") or f.get("booktitle") or f.get("journal") or ""
    pages = f.get("pages", "")
    extra = f" {pages}" if pages else ""
    line = f"{bold_name(authors)} ({year}). {latex_escape(title)}. "
    if venue:
        line += r"\textit{" + latex_escape(venue) + "}"
    if extra:
        line += "," + latex_escape(extra)
    line += "."
    return line


def find_pdflatex():
    candidates = [
        os.environ.get("PDFLATEX", ""),
        shutil.which("pdflatex") or "",
        "/Library/TeX/texbin/pdflatex",
        "/usr/local/texlive/2026/bin/universal-darwin/pdflatex",
        "/usr/local/texlive/2025/bin/universal-darwin/pdflatex",
        "/opt/homebrew/bin/pdflatex",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


# --------------------------------------------------------------------------
# CV rendering
# --------------------------------------------------------------------------

def render(cv, bib, include_patents):
    L = [TEX_PREAMBLE]

    b = cv.get("basics", {})
    loc = b.get("location", {})
    L.append(r"\begin{center}")
    L.append(r"\cvname{" + latex_escape(b.get("name", "")) + r"}")
    L.append(r"\\[2pt]")
    contact = " • ".join(x for x in [
        b.get("email", ""),
        b.get("phone", ""),
        b.get("website", ""),
        ", ".join(x for x in [loc.get("city", ""), loc.get("region", ""),
                              {"CN": "China"}.get(loc.get("countryCode", ""), loc.get("countryCode", ""))] if x),
    ] if x)
    L.append(r"\cvcontact{" + latex_escape(contact) + r"}")
    if b.get("summary"):
        L.append(r"\\[2pt]")
        L.append(r"\cvcontact{\textit{" + latex_escape(b["summary"]) + r"}}")
    L.append(r"\end{center}")

    def section(title):
        L.append(r"\section*{" + latex_escape(title) + r"}")

    def itemize(items):
        if not items:
            return
        L.append(r"\begin{itemize}[leftmargin=1.2em,itemsep=1pt,topsep=2pt]")
        for it in items:
            L.append(r"\item " + latex_escape(it))
        L.append(r"\end{itemize}")

    # Professional Experience
    section("Professional Experience")
    for w in cv.get("work", []):
        dates = " – ".join(x for x in [w.get("startDate", ""), w.get("endDate", "")] if x)
        L.append(r"\textbf{" + latex_escape(w.get("position", "")) + r"}, " +
                 latex_escape(w.get("organization", "")) +
                 (r" \hfill \textit{" + latex_escape(dates) + r"}" if dates else ""))
        if w.get("summary"):
            L.append(latex_escape(w["summary"]))
        itemize(w.get("highlights", []))

    # Education
    section("Education")
    for e in cv.get("education", []):
        dates = " – ".join(x for x in [e.get("startDate", ""), e.get("endDate", "")] if x)
        L.append(r"\textbf{" + latex_escape(e.get("area", "")) + r"}, " +
                 latex_escape(e.get("institution", "")) +
                 (r" \hfill \textit{" + latex_escape(dates) + r"}" if dates else ""))
        if e.get("summary"):
            L.append(latex_escape(e["summary"]))

    # Research Projects
    section("Research Projects")
    total = [p for p in cv.get("projects", []) if "Total Research Funding" in p.get("name", "")]
    if total:
        L.append(latex_escape(total[0].get("summary", "")))
    by_org = {}
    for p in cv.get("projects", []):
        if "Total Research Funding" in p.get("name", ""):
            continue
        by_org.setdefault(p.get("organization", "Other"), []).append(p)
    for org, plist in by_org.items():
        L.append(r"\textbf{" + latex_escape(org) + r"}")
        for p in plist:
            role = p.get("role", "")
            years = " – ".join(x for x in [p.get("startDate", ""), p.get("endDate", "")] if x)
            bits = [p.get("name", "")]
            if role:
                bits.append(f"({role})")
            if years:
                bits.append(f"{years}")
            if p.get("summary"):
                bits.append(p["summary"])
            L.append(r"\begin{itemize}[leftmargin=1.2em,itemsep=1pt,topsep=2pt]")
            L.append(r"\item " + latex_escape(", ".join(bits)))
            L.append(r"\end{itemize}")

    # Publications
    section("Publications")
    groups = [
        ("Representative Publications", "representative"),
        ("Other Publications (Reverse Chronological Order)", "other"),
        ("Preprints / Under Review", "preprint"),
        ("Thesis", "thesis"),
    ]
    for heading, g in groups:
        items = [p for p in cv.get("publications", []) if p.get("group") == g]
        if not items:
            continue
        L.append(r"\textbf{" + latex_escape(heading) + r"}")
        L.append(r"\begin{itemize}[leftmargin=1.2em,itemsep=2pt,topsep=2pt]")
        for p in items:
            L.append(r"\item " + fmt_pub(p, bib))
        L.append(r"\end{itemize}")

    # Supervision
    if cv.get("supervision"):
        section("Student Supervision and Mentorship")
        itemize(cv["supervision"])

    # Honors & Awards
    if cv.get("awards"):
        section(r"Honors \& Awards")
        L.append(r"\begin{itemize}[leftmargin=1.2em,itemsep=2pt,topsep=2pt]")
        for a in cv["awards"]:
            parts = []
            if a.get("title"):
                parts.append(r"\textbf{" + latex_escape(a["title"]) + r"}")
            if a.get("event"):
                parts.append(latex_escape(a["event"]))
            if a.get("date"):
                parts.append(f"({latex_escape(a['date'])})")
            if a.get("role"):
                parts.append(latex_escape(a["role"]))
            if a.get("summary"):
                parts.append(latex_escape(a["summary"]))
            L.append(r"\item " + " | ".join(parts))
        L.append(r"\end{itemize}")

    # Academic Services
    sv = cv.get("service", {})
    if any(sv.values()):
        section("Academic Services")
        blocks = [
            ("Journal Editorial Roles", sv.get("editorial", [])),
            ("Conference Program Committees", sv.get("program_committees", [])),
            ("Conference Reviewer", sv.get("conference_reviewer", [])),
            ("Journal Reviewer Roles", sv.get("journal_reviewer", [])),
            ("Reviewer Recognition", sv.get("recognition", [])),
        ]
        for heading, items in blocks:
            if not items:
                continue
            L.append(r"\textbf{" + latex_escape(heading) + r"}")
            itemize(items)

    # Granted Patents (optional, from the LOCAL gitignored file)
    if include_patents and PATENTS_YML.exists():
        try:
            import yaml
            data = yaml.safe_load(PATENTS_YML.read_text(encoding="utf-8")) or {}
            granted = [p for p in data.get("patents", []) if p.get("status") == "granted"]
        except Exception:
            granted = []
        if granted:
            section("Granted Patents")
            L.append(r"\begin{itemize}[leftmargin=1.2em,itemsep=2pt,topsep=2pt]")
            for p in granted:
                bits = [p.get("title", "")]
                if p.get("number"):
                    bits.append("Patent No. " + p["number"])
                if p.get("grant_number"):
                    bits.append(p["grant_number"])
                if p.get("grant_date"):
                    bits.append("Granted: " + p["grant_date"])
                if p.get("rank"):
                    bits.append("Rank " + p["rank"])
                L.append(r"\item " + latex_escape(", ".join(bits)))
            L.append(r"\end{itemize}")

    # Other Academic Activities
    if cv.get("activities"):
        section("Other Academic Activities")
        itemize(cv["activities"])

    # Impacts
    imp = cv.get("impacts", {})
    if imp.get("industry") or imp.get("media"):
        section("Impacts")
        if imp.get("industry"):
            L.append(r"\textbf{Industry Contributions}")
            itemize(imp["industry"])
        if imp.get("media"):
            L.append(r"\textbf{Media Recognition}")
            itemize(imp["media"])

    L.append(TEX_END)
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cv", default=str(DEFAULT_CV))
    ap.add_argument("--bib", default=str(DEFAULT_BIB))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--tex-out", default="", help="write the .tex to this path")
    ap.add_argument("--dry-run", action="store_true", help="only write/print the .tex, do not compile")
    ap.add_argument("--keep-tex", action="store_true", help="keep the .tex next to the output PDF")
    ap.add_argument("--patents", action="store_true", help="include Granted Patents from the local (gitignored) _data/patents.yml")
    args = ap.parse_args()

    cv = json.loads(Path(args.cv).read_text(encoding="utf-8"))
    bib = parse_bib(args.bib)
    tex = render(cv, bib, args.patents)

    if args.tex_out:
        Path(args.tex_out).write_text(tex, encoding="utf-8")
        print(f"[tex] {args.tex_out}")

    if args.dry_run:
        print(tex)
        print("[dry-run] 未编译。去掉 --dry-run 编译 PDF。")
        return

    pdflatex = find_pdflatex()
    if not pdflatex:
        print("[error] 未找到 pdflatex（可设 PDFLATEX 环境变量或安装 MacTeX）", file=sys.stderr)
        sys.exit(1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tex_path = Path(tmp) / "cv.tex"
        tex_path.write_text(tex, encoding="utf-8")
        proc = subprocess.run(
            [pdflatex, "-interaction=nonstopmode", "-halt-on-error", "cv.tex"],
            cwd=tmp, capture_output=True, text=True,
        )
        pdf = Path(tmp) / "cv.pdf"
        if not pdf.exists():
            print(proc.stdout[-2000:], file=sys.stderr)
            print("[error] pdflatex 编译失败", file=sys.stderr)
            sys.exit(1)
        shutil.copy(pdf, out)
    print(f"[pdf] {out} ({out.stat().st_size} bytes)")

    if args.keep_tex:
        keep = out.with_suffix(".tex")
        keep.write_text(tex, encoding="utf-8")
        print(f"[tex] {keep}")


if __name__ == "__main__":
    main()
