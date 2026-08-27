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
        nt = tokens(item.get("text", ""))
        if not any(len(nt & tokens(t)) >= 2 for t in award_texts):
            errors.append(
                f"news award 无对应 awards.yml 条目: {item.get('date_display','?')} - {item.get('text','')[:60]}"
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


def check_file_refs(*datasets, errors):
    refs = []
    for ds in datasets:
        for item in ds if isinstance(ds, list) else []:
            if not isinstance(item, dict):
                continue
            for k, v in item.items():
                if isinstance(v, str) and v.startswith(("/files/", "/images/")):
                    refs.append(v)
                if k == "links" and isinstance(v, list):
                    for link in v:
                        if isinstance(link, dict) and str(link.get("url", "")).startswith(("/files/", "/images/")):
                            refs.append(link["url"])
    for ref in sorted(set(refs)):
        rel = ref.lstrip("/")
        if not (ROOT / rel).exists():
            errors.append(f"引用的文件不存在: {ref}")


def check_service_rendered(service, site_dir, errors):
    idx = Path(site_dir) / "index.html"
    if not idx.exists():
        errors.append(f"站点未构建: {idx}（先运行 bundle exec jekyll build）")
        return
    text = idx.read_text(encoding="utf-8")
    m = re.search(r'<h2 id="professional-services">(.*?)<h2 id="industry-impact">', text, re.S)
    if not m:
        errors.append("首页未找到 Professional Services 区块")
        return
    rendered = normalize(m.group(1))
    for section in service.get("sections", []):
        for entry in section.get("entries", []):
            items = entry.get("items") if entry.get("type") == "list" else [entry.get("text", "")]
            for it in items:
                norm = normalize(it)
                if not norm:
                    continue
                if norm not in rendered:
                    errors.append(f"service.yml 条目未出现在渲染结果: {it[:60]}")


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

    print(f"news: {len(news)} | awards: {len(awards)} | service sections: {len(service.get('sections', []))} | patents: {len(patents.get('patents', []))}")
    if errors:
        print(f"[FAIL] {len(errors)} 处不一致：")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("[OK] 一致性检查全部通过")


if __name__ == "__main__":
    main()
