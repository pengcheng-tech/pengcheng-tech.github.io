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
  4. Every entry in _data/service.yml appears in the rendered /activities/
     page (_site/activities/index.html).
  5. Every news `evidence` field contains no URL or email address (evidence
     records source and date only, per the update-workflow security rules).
  6. Every list item has a sortable date field (`date_sort`; patents use
     `grant_date`). WARN mode during data migration (flips to error once
     service/awards are fully migrated).
  7. Rendered pages show list items in descending `date_sort` order. WARN
     mode during data migration.

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


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def check_evidence_security(news, errors):
    """evidence 字段只记来源与日期：禁止 URL 与邮件地址（防泄个人授权 token / 收件人）。"""
    for item in news:
        if not isinstance(item, dict):
            continue
        ev = item.get("evidence")
        if not ev:
            continue
        ev = str(ev)
        if re.search(r"https?://|www\.", ev, re.IGNORECASE):
            errors.append(
                f"news 条目 evidence 含 URL（只记来源与日期）: {item.get('date_display','?')} - {ev[:60]}"
            )
        if EMAIL_RE.search(ev):
            errors.append(
                f"news 条目 evidence 含邮件地址（只记来源与日期）: {item.get('date_display','?')} - {ev[:60]}"
            )


SERVICE_ALPHA_SORT = "alpha"  # Journal Reviewer 例外：持续性服务，按刊物名字母序，不参与时间倒序


def _entry_text(entry):
    """service 的 bullet / featured 条目兼容字符串与对象（迁移后为 {text, date_sort, ...}）。"""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return entry.get("text", "")
    return ""


def check_dates_present(news, service, awards, patents, warnings):
    """warn 模式：每个列表条目必须有排序日期字段（news/service/awards 用 date_sort，patents 用 grant_date）。

    全部数据迁移完成后（date-sort 系列 PR 收尾）改为 error。Journal Reviewer 组（sort: alpha）豁免。
    """
    for item in news:
        if not isinstance(item, dict) or item.get("commented"):
            continue
        if not item.get("date_sort"):
            warnings.append(f"news 条目缺 date_sort: {item.get('date_display','?')} - {item.get('text','')[:40]}")
    for a in awards if isinstance(awards, list) else []:
        if isinstance(a, dict) and not a.get("date_sort"):
            warnings.append(f"awards 条目缺 date_sort: {a.get('title','?')[:60]}")
    featured = service.get("featured", []) if isinstance(service, dict) else []
    for f in featured:
        if not (isinstance(f, dict) and f.get("date_sort")):
            warnings.append(f"service featured 条目缺 date_sort: {_entry_text(f)[:50]}")
    sections = service.get("sections", []) if isinstance(service, dict) else []
    for section in sections:
        for group in section.get("groups", []):
            if group.get("sort") == SERVICE_ALPHA_SORT:
                continue  # 例外：期刊审稿按字母序固定排列，不参与时间排序
            for b in group.get("bullets", []):
                if not (isinstance(b, dict) and b.get("date_sort")):
                    warnings.append(f"service bullet 缺 date_sort: {_entry_text(b)[:50]}")
    patents_list = patents.get("patents", []) if isinstance(patents, dict) else []
    for p in patents_list:
        if isinstance(p, dict) and not p.get("grant_date"):
            warnings.append(f"patent 条目缺 grant_date: {p.get('title','?')[:40]}")


def check_rendering_order(items, rendered, label, warnings):
    """warn 模式：条目在渲染产物中的出现位置必须按 date_sort 倒序。

    items: list of (search_text, date_sort)；缺 date_sort 的条目由 check_dates_present 提示，此处跳过。
    - 按 date_sort 分组（降序）：**新日期组的全部条目必须整体出现在旧日期组之前**。
    - 同 date_sort 的条目顺序**不受保证**（Liquid `sort | reverse` 对同键条目无稳定序），不校验组内顺序。
    - 位置用 rfind（最后一次出现）：条目文本若同时出现在更靠前的区块（如奖项名出现在新闻里），
      取所属区块中的那次出现。
    """
    dated = []
    for text, ds in items:
        if not ds:
            continue
        n = normalize(text)
        if not n:
            continue
        dated.append((ds, rendered.rfind(n), text))
    dated.sort(key=lambda t: t[0], reverse=True)
    groups = []
    for ds, pos, text in dated:
        if groups and groups[-1][0] == ds:
            groups[-1][1].append((pos, text))
        else:
            groups.append((ds, [(pos, text)]))
    prev_max = -1
    for ds, members in groups:
        positions = [p for p, _ in members if p >= 0]
        for pos, text in members:
            if pos < 0:
                warnings.append(f"{label}: 条目未在渲染产物中找到: {text[:50]}")
        if positions:
            lo, hi = min(positions), max(positions)
            if lo < prev_max:
                warnings.append(
                    f"{label}: 渲染顺序与 date_sort 倒序不符: {members[0][1][:50]} (date_sort={ds} 的条目早于更晚日期组出现)"
                )
            prev_max = hi


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
                text = _entry_text(b)
                norm = normalize(text)
                if not norm:
                    continue
                if norm not in rendered:
                    errors.append(f"service.yml 条目未出现在 /activities/ 渲染结果: {text[:60]}")


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
        values.append(_entry_text(f))
    for section in service.get("sections", []) if isinstance(service, dict) else []:
        for group in section.get("groups", []):
            for b in group.get("bullets", []):
                values.append(_entry_text(b))
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
    warnings = []
    bib_keys = set(parse_bib(bib_path))
    if not bib_keys:
        errors.append(f"publications.bib 解析为空: {bib_path}")

    check_award_news(news, awards, errors)
    check_publication_news(news, bib_keys, errors)
    check_evidence_security(news, errors)
    check_file_refs(news, awards, service, patents, errors=errors)
    check_service_rendered(service, site_dir, errors)
    check_hardcoded_duplication(yml_values(news, awards, service, patents), ROOT / "_pages", errors)

    # ---- 日期字段存在性 + 渲染倒序（warn 模式；全部数据迁移完成后改为 error）----
    check_dates_present(news, service, awards, patents, warnings)

    homepage = Path(site_dir) / "index.html"
    if homepage.exists():
        home_html = normalize(homepage.read_text(encoding="utf-8"))
        news_pairs = [
            (f"{i.get('date_display','')}: {i.get('text','')}", i.get("date_sort"))
            for i in news if isinstance(i, dict) and not i.get("commented")
        ]
        check_rendering_order(news_pairs, home_html, "首页 Recent News", warnings)
        feat_pairs = []
        if isinstance(service, dict):
            for f in service.get("featured", []):
                feat_pairs.append((_entry_text(f), f.get("date_sort") if isinstance(f, dict) else None))
        check_rendering_order(feat_pairs, home_html, "首页 Professional Services", warnings)
        aw_feat = [
            (a.get("title", ""), a.get("date_sort"))
            for a in awards if isinstance(a, dict) and a.get("featured")
        ]
        check_rendering_order(aw_feat, home_html, "首页 Awards", warnings)

    activities = Path(site_dir) / "activities" / "index.html"
    if activities.exists():
        act_html = normalize(activities.read_text(encoding="utf-8"))
        for section in service.get("sections", []) if isinstance(service, dict) else []:
            for group in section.get("groups", []):
                if group.get("sort") == SERVICE_ALPHA_SORT:
                    continue
                pairs = [
                    (_entry_text(b), b.get("date_sort") if isinstance(b, dict) else None)
                    for b in group.get("bullets", [])
                ]
                check_rendering_order(pairs, act_html, f"/activities/ {group.get('title','')}", warnings)

    awards_page = Path(site_dir) / "awards" / "index.html"
    if awards_page.exists():
        aw_html = normalize(awards_page.read_text(encoding="utf-8"))
        for cat in ("research", "reviewer", "academic", "mentorship", "industry", "media"):
            pairs = [
                (a.get("title", ""), a.get("date_sort"))
                for a in awards if isinstance(a, dict) and a.get("category") == cat
            ]
            if pairs:
                check_rendering_order(pairs, aw_html, f"/awards/ {cat}", warnings)

    print(f"news: {len(news)} | awards: {len(awards)} | service sections: {len(service.get('sections', []))} | patents: {len(patents.get('patents', []))}")
    if warnings:
        print(f"[WARN] {len(warnings)} 处（日期字段 / 渲染顺序：迁移期间仅警告，全部迁移完成后将改为 error）：")
        for w in warnings:
            print("  -", w)
    if errors:
        print(f"[FAIL] {len(errors)} 处不一致：")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("[OK] 一致性检查全部通过")


if __name__ == "__main__":
    main()
