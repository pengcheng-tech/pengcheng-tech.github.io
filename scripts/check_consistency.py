#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_consistency.py — Cross-file consistency checks for the site data.

Run after editing _data/*.yml / publications.bib and rebuilding the site
(scripts/update-site flow). Fails (exit 1) on any inconsistency and prints
the details; the update-site workflow treats a failure as a stop signal.

Checks:
  1. Every news entry typed "award" has a matching entry in _data/awards.yml.
  2. Every news entry typed "publication" resolves to an entry in
     publications.bib (via the `paper` key, or by quoted-title fuzzy match).
  3. Every /files/ (and /images/) path referenced from the yml data files
     actually exists in the repository.
  4. Every entry in _data/service.yml appears in the rendered
     Professional Services section of the built homepage (_site/index.html).

Usage:
  python3 scripts/check_consistency.py
  python3 scripts/check_consistency.py --site _site --bib publications.bib
"""

import argparse
import html
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[error] PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data"


def load_yaml(name):
    path = DATA / name
    if not path.exists():
        return {}  # optional data file (e.g. gitignored patents.yml) may be absent
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def normalize(text):
    """Lowercase, strip markdown/HTML artifacts and normalize quotes."""
    if not text:
        return ""
    t = str(text)
    t = re.sub(r"\*\*|__|\*|_", "", t)
    t = re.sub(r"\[\[[^\]]*\]\]\([^)]*\)", "", t)  # markdown links -> label only
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+([,.;:)\]])", r"\1", t)  # tag stripping leaves "word ," -> "word,"
    t = html.unescape(t)
    for a, b in (("\u201c", '"'), ("\u201d", '"'), ("\u2018", "'"), ("\u2019", "'")):
        t = t.replace(a, b)
    t = t.lower()
    return re.sub(r"\s+", " ", t).strip()


def tokens(text):
    return {w for w in re.findall(r"[a-z0-9]{4,}", normalize(text))}


def parse_bib(path):
    """Minimal BibTeX parser: return dict key -> fields."""
    text = Path(path).read_text(encoding="utf-8")
    entries = {}
    for m in re.finditer(r"@\s*[A-Za-z]+\s*\{\s*([^,]+)\s*,", text):
        entries[m.group(1).strip()] = True
    return entries


def check_award_news(news, awards, errors):
    award_texts = []
    for a in awards:
        if isinstance(a, dict):
            award_texts.append(normalize(" ".join(str(a.get(k, "")) for k in ("title", "event", "detail"))))
    for item in news:
        if not isinstance(item, dict) or item.get("type") != "award":
            continue
        if item.get("awards_entry") is False:
            # explicit exemption: the news is an award-type announcement that is
            # intentionally NOT listed on the /awards/ page (e.g. honorary
            # memberships) — kept typed "award" so other checks still apply.
            continue
        nt = tokens(item.get("text", ""))
        if not any(len(nt & tokens(t)) >= 2 for t in award_texts):
            errors.append(
                f"news award 无对应 awards.yml 条目（如需豁免请加 awards_entry: false）: {item.get('date_display','?')} - {item.get('text','')[:60]}"
            )


def check_publication_news(news, bib_keys, errors):
    for item in news:
        if not isinstance(item, dict) or item.get("type") != "publication":
            continue
        key = item.get("paper", "").strip()
        if key:
            if key not in bib_keys:
                errors.append(f"news publication 的 paper key 不在 publications.bib: {key}")
            continue
        # fall back to a quoted title in the text
        m = re.search(r'"([^"]+)"', item.get("text", ""))
        if not m:
            errors.append(
                f"news type=publication 缺 paper key 且文本无标题可匹配: {item.get('text','')[:60]}"
            )
            continue
        nt = tokens(m.group(1))
        if not any(nt & tokens(k) for k in bib_keys):
            errors.append(f"news 提及的论文未在 publications.bib 找到: {m.group(1)[:60]}")


def _walk_refs(node, refs):
    """Recursively collect /files/ and /images/ references from yml structures."""
    if isinstance(node, str):
        if node.startswith(("/files/", "/images/")):
            refs.add(node)
        return
    if isinstance(node, dict):
        for v in node.values():
            _walk_refs(v, refs)
    elif isinstance(node, list):
        for v in node:
            _walk_refs(v, refs)


def check_file_refs(*datasets, errors):
    """Every /files/ and /images/ path referenced from the yml data must exist."""
    refs = set()
    for ds in datasets:
        if isinstance(ds, list):
            for item in ds:
                _walk_refs(item, refs)
        elif isinstance(ds, dict):
            _walk_refs(ds, refs)
    for ref in sorted(refs):
        rel = ref.lstrip("/")
        if not (ROOT / rel).exists():
            errors.append(f"引用的文件不存在: {ref}")


def check_service_rendered(service, site_dir, errors):
    """Every service.yml bullet must appear in the rendered /activities/ page."""
    idx = Path(site_dir) / "activities" / "index.html"
    if not idx.exists():
        errors.append(f"站点未构建: {idx}（先运行 bundle exec jekyll build）")
        return
    rendered = normalize(idx.read_text(encoding="utf-8"))
    for section in service.get("sections", []):
        for group in section.get("groups", []):
            for b in group.get("bullets", []):
                norm = normalize(b)
                if not norm:
                    continue
                if norm not in rendered:
                    errors.append(f"service.yml 条目未出现在 /activities/ 渲染结果: {b[:60]}")


def yml_values(news, awards, service, patents):
    """Collect normalized, substantial string values from the yml data files."""
    values = []
    for item in news if isinstance(news, list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("text"):
            values.append(item["text"])
        for link in item.get("links", []) if isinstance(item.get("links"), list) else []:
            if link.get("label"):
                values.append(link["label"])
    for a in awards if isinstance(awards, list) else []:
        if not isinstance(a, dict):
            continue
        for k in ("title", "event", "subtitle"):
            if a.get(k):
                values.append(a[k])
        for b in a.get("bullets", []) if isinstance(a.get("bullets"), list) else []:
            if b.get("text"):
                values.append(b["text"])
        if a.get("note"):
            values.append(a["note"])
        if a.get("quote"):
            values.append(a["quote"])
    for f in service.get("featured", []) if isinstance(service, dict) else []:
        values.append(f)
    for section in service.get("sections", []) if isinstance(service, dict) else []:
        for group in section.get("groups", []):
            for b in group.get("bullets", []):
                values.append(b)
    return [normalize(v) for v in values if v]


def check_hardcoded_duplication(values, pages_dir, errors):
    """Flag _pages/*.md that hardcode content already in _data/*.yml.

    A page that renders from yml (Liquid) never contains the value literally;
    a literal occurrence means the content is duplicated by hand and the page
    would drift from the data source (this is the bug that let USENIX / IJCAI
    stay missing from pages).
    """
    pages_dir = Path(pages_dir)
    if not pages_dir.is_dir():
        return
    for page in sorted(pages_dir.glob("*.md")):
        content = normalize(page.read_text(encoding="utf-8"))
        for v in values:
            if len(v) < 25:  # skip short values to avoid noise
                continue
            if v in content:
                errors.append(f"{page.name} 硬编码了 _data/*.yml 的内容: {v[:70]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", default="", help="built site dir (default <repo>/_site)")
    ap.add_argument("--bib", default="", help="path to publications.bib (default <repo>/publications.bib)")
    args = ap.parse_args()

    site_dir = Path(args.site) if args.site else ROOT / "_site"
    bib_path = Path(args.bib) if args.bib else ROOT / "publications.bib"

    news = load_yaml("news.yml") or []
    awards = load_yaml("awards.yml") or []
    service = load_yaml("service.yml") or {}
    patents = load_yaml("patents.yml") or {}

    errors = []
    bib_keys = set(parse_bib(bib_path))
    if not bib_keys:
        errors.append(f"publications.bib 解析为空: {bib_path}")

    check_award_news(news, awards, errors)
    check_publication_news(news, bib_keys, errors)
    check_file_refs(news, awards, service, patents, errors=errors)
    check_service_rendered(service, site_dir, errors)
    check_hardcoded_duplication(yml_values(news, awards, service, patents), ROOT / "_pages", errors)

    print(f"news: {len(news)} | awards: {len(awards)} | service sections: {len(service.get('sections', []))} | patents: {len(patents.get('patents', []))}")
    if errors:
        print(f"[FAIL] {len(errors)} 处不一致：")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("[OK] 一致性检查全部通过")


if __name__ == "__main__":
    main()
