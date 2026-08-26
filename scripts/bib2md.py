#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bib2md.py — Generate AcademicPages publication markdown from publications.bib.

publications.bib is the single source of truth. Manually editing it works
exactly like running scripts/sync_orcid.py: after editing, regenerate the
markdown and commit the result.

For every entry in publications.bib this script writes
    _publications/YYYY-MM-DD-<key>.md
whose front matter follows the AcademicPages spec as used in this repository:
title, collection, category, permalink, excerpt, date, venue, paperurl,
bibtexurl, citation (plus optional codeurl).

Custom bib fields understood (in addition to standard BibTeX fields):
  category   -> collection category: conferences | manuscripts | undergoing
                (default: conferences)
  date       -> display date YYYY-MM-DD; decides the filename and front matter
                (default: <year>-01-01)
  venue      -> human-readable venue string (default: booktitle/journal)
  excerpt    -> one-line teaser shown on list pages (default: empty)
  citation   -> full formatted citation string (default: empty)
  codeurl    -> optional code repository link
  permalink  -> optional explicit permalink (default: /publication/<year>-<key>)

A ready-to-fill template for a manually added entry lives at
scripts/new-entry-template.bib.

Manual workflow (same effect as sync_orcid.py):
  1. edit publications.bib (add/change/remove entries)
  2. python3 scripts/bib2md.py --prune     # regenerate _publications/
  3. bundle exec jekyll build              # verify
  4. commit and open a PR

Usage:
  python3 scripts/bib2md.py --dry-run
  python3 scripts/bib2md.py --dry-run --bib publications.bib --out _publications
  python3 scripts/bib2md.py                # real mode: writes/updates md files
  python3 scripts/bib2md.py --prune        # also remove md files not in the bib
"""

import argparse
import os
import re
import sys
from datetime import date

BIB_DEFAULT = "publications.bib"
OUT_DEFAULT = "_publications"


# --------------------------------------------------------------------------
# Minimal BibTeX parsing (stdlib only)
# --------------------------------------------------------------------------

def parse_bib(path):
    """Return list of (bibtype, key, field_dict).

    Handles nested braces inside field values (e.g. LaTeX macros or
    brace-protected strings) with a depth-counting scanner.
    """
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    entries = []
    i, n = 0, len(text)
    while i < n:
        m = re.compile(r"@\s*([A-Za-z]+)\s*\{").search(text, i)
        if not m:
            break
        bibtype = m.group(1).lower()
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
        entries.append((bibtype, key, fields))
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


# --------------------------------------------------------------------------
# Entry -> front matter
# --------------------------------------------------------------------------

def pick_date(fields):
    """Return (yyyy, mm, dd) from the custom `date` field, else from `year`."""
    d = fields.get("date", "")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", d)
    if m:
        return m.group(1), m.group(2), m.group(3)
    year = fields.get("year", "1900")
    m2 = re.match(r"(\d{4})", year)
    y = m2.group(1) if m2 else "1900"
    return y, "01", "01"


def front_matter(fields, key, bibtype):
    y, mo, dd = pick_date(fields)
    permalink = fields.get("permalink") or f"/publication/{y}-{key}"

    category = fields.get("category", "conferences")
    if category not in ("conferences", "manuscripts", "undergoing"):
        print(f"[warn] {key}: unknown category '{category}', using 'conferences'", file=sys.stderr)
        category = "conferences"

    venue = (
        fields.get("venue")
        or fields.get("booktitle")
        or fields.get("journal")
        or ""
    )
    title = fields.get("title", "")
    excerpt = fields.get("excerpt", "")
    citation = fields.get("citation", "")
    paperurl = fields.get("url", "")
    codeurl = fields.get("codeurl", "")
    bibtexurl = fields.get("bibtexurl", "")

    lines = ["---"]
    lines.append(f'title: "{escape_yaml(title)}"')
    lines.append("collection: publications")
    lines.append(f"category: {category}")
    lines.append(f"permalink: {permalink}")
    lines.append(f"excerpt: '{escape_single(excerpt)}'")
    lines.append(f"date: {y}-{mo}-{dd}")
    lines.append(f"venue: '{escape_single(venue)}'")
    lines.append(f"paperurl: '{escape_single(paperurl)}'")
    lines.append(f"bibtexurl: '{escape_single(bibtexurl)}'")
    lines.append(f"citation: '{escape_single(citation)}'")
    if codeurl:
        lines.append(f"codeurl: '{escape_single(codeurl)}'")
    lines.append("---")
    return "\n".join(lines) + "\n"


def escape_yaml(s):
    """Escape double quotes inside a double-quoted YAML scalar."""
    return s.replace('"', '\\"')


def escape_single(s):
    """Escape single quotes inside a single-quoted YAML scalar."""
    return s.replace("'", "''")


def md_filename(fields, key):
    y, mo, dd = pick_date(fields)
    return f"{y}-{mo}-{dd}-{key}.md"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print what would be generated without writing")
    ap.add_argument("--bib", default=BIB_DEFAULT, help=f"path to .bib file (default {BIB_DEFAULT})")
    ap.add_argument("--out", default=OUT_DEFAULT, help=f"output directory (default {OUT_DEFAULT})")
    ap.add_argument("--prune", action="store_true", help="delete md files in --out that are not generated from the current bib (real mode only)")
    args = ap.parse_args()

    try:
        entries = parse_bib(args.bib)
    except FileNotFoundError:
        print(f"[error] {args.bib} not found.", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print(f"[error] no entries parsed from {args.bib}", file=sys.stderr)
        sys.exit(1)

    generated = []
    for bibtype, key, fields in entries:
        fm = front_matter(fields, key, bibtype)
        fname = md_filename(fields, key)
        generated.append((fname, key, fm))

    # what already exists / what would change
    os.makedirs(args.out, exist_ok=True)
    changes = 0
    for fname, key, fm in generated:
        path = os.path.join(args.out, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                old = fh.read()
            status = "same" if old == fm else "update"
        else:
            status = "new"
        if status != "same":
            changes += 1
        if args.dry_run or status != "same":
            print(f"[{status:6s}] {path}")
            if args.dry_run:
                print(fm)
                print()

    print(f"[summary] {len(generated)} entries in {args.bib}; {changes} file(s) would change")

    if args.prune:
        existing = {f for f in os.listdir(args.out) if f.endswith(".md")}
        wanted = {fname for fname, _, _ in generated}
        orphans = sorted(existing - wanted)
        print(f"[prune] {len(orphans)} existing md file(s) not generated from {args.bib}:")
        for f in orphans:
            print(f"  would remove: {os.path.join(args.out, f)}")

    if args.dry_run:
        print("[dry-run] no files were written. Re-run without --dry-run to generate.")
        return

    # real mode
    for fname, key, fm in generated:
        path = os.path.join(args.out, fname)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fm)
    if args.prune:
        existing = {f for f in os.listdir(args.out) if f.endswith(".md")}
        wanted = {fname for fname, _, _ in generated}
        for f in sorted(existing - wanted):
            os.remove(os.path.join(args.out, f))
            print(f"[removed] {os.path.join(args.out, f)}")
    print(f"[done] wrote {len(generated)} file(s) to {args.out}")


if __name__ == "__main__":
    main()
