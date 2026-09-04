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
     `grant_date`). Groups marked `sort: none` are exempt.
  7. Rendered pages show list items in descending `date_sort` order.
  8. Consumer products keep the global reverse-chronological rule:
     export_obsidian.py outputs (news / awards / service date-groups by
     `date_sort`, patents by `grant_date`) and the CV LaTeX render
     (work / education by startDate, publications per group by bib date,
     awards by date, granted patents by grant_date).
  9. The /cv/ page renders cv.json lists newest-first (work / education /
     awards / per-group publications).
 10. cv.json mirrors the site data: yml awards of categories
     research/reviewer/academic/mentorship must appear in cv.json Honors &
     Awards; industry/media must be represented in cv.json impacts;
     date-sorted service venue codes (e.g. "ICLR 2027") must appear in
     cv.json service text.

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


SERVICE_NONE_SORT = "none"  # 手工顺序组（期刊审稿按刊物分量排序、Editorial 描述性 bullet）：不参与时间排序


def _entry_text(entry):
    """service 的 bullet / featured 条目兼容字符串与对象（迁移后为 {text, date_sort, ...}）。"""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return entry.get("text", "")
    return ""


def check_dates_present(news, service, awards, patents, errors):
    """每个列表条目必须有排序日期字段（news/service/awards 用 date_sort，patents 用 grant_date）。

    `sort: none` 组（期刊审稿按分量手工排序、描述性 bullet）豁免。
    """
    for item in news:
        if not isinstance(item, dict) or item.get("commented"):
            continue
        if not item.get("date_sort"):
            errors.append(f"news 条目缺 date_sort: {item.get('date_display','?')} - {item.get('text','')[:40]}")
    for a in awards if isinstance(awards, list) else []:
        if isinstance(a, dict) and not a.get("date_sort"):
            errors.append(f"awards 条目缺 date_sort: {a.get('title','?')[:60]}")
    featured = service.get("featured", []) if isinstance(service, dict) else []
    for f in featured:
        if not (isinstance(f, dict) and f.get("date_sort")):
            errors.append(f"service featured 条目缺 date_sort: {_entry_text(f)[:50]}")
    sections = service.get("sections", []) if isinstance(service, dict) else []
    for section in sections:
        for group in section.get("groups", []):
            if group.get("sort") == SERVICE_NONE_SORT:
                continue  # 例外：none（期刊审稿按分量手工排序 / 描述性 bullet）不参与时间排序
            for b in group.get("bullets", []):
                if not (isinstance(b, dict) and b.get("date_sort")):
                    errors.append(f"service bullet 缺 date_sort: {_entry_text(b)[:50]}")
    patents_list = patents.get("patents", []) if isinstance(patents, dict) else []
    for p in patents_list:
        if isinstance(p, dict) and not p.get("grant_date"):
            errors.append(f"patent 条目缺 grant_date: {p.get('title','?')[:40]}")


def check_rendering_order(items, rendered, label, errors):
    """条目在渲染产物中的出现位置必须按 date_sort 倒序。

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
                errors.append(f"{label}: 条目未在渲染产物中找到: {text[:50]}")
        if positions:
            lo, hi = min(positions), max(positions)
            if lo < prev_max:
                errors.append(
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


def _seq_is_desc(seq, label, errors):
    """断言 date 序列按倒序（等于其稳定降序排序结果，含同值并列）。"""
    if seq != sorted(seq, reverse=True):
        for i, (a, b) in enumerate(zip(seq, sorted(seq, reverse=True))):
            if a != b:
                errors.append(f"{label}: 产物顺序非倒序（第 {i + 1} 项 {a!r}，期望 {b!r}）")
                return


def _verify_joined_service_line(items, joined, label, errors):
    """cv service date 块的 join 渲染行校验：每段名字都在块内且顺序按 date_sort 倒序。
    单条目块（editorial / recognition）跳过顺序校验。"""
    if len(items) <= 1:
        return
    name2ds = {it.get("name", ""): it.get("date_sort", "") for it in items if isinstance(it, dict)}
    seq = [name2ds.get(n.strip(), "") for n in joined.split(",")]
    _seq_is_desc(seq, label, errors)


def check_consumer_export_order(news, service, awards, patents, errors):
    """export_obsidian.py 产物（Obsidian md）必须按 date_sort / grant_date 倒序。"""
    import export_obsidian as ex

    news_text2ds = {}
    for item in news:
        if isinstance(item, dict) and not item.get("commented"):
            news_text2ds[normalize(ex.strip_md(item.get("text", "")))] = item.get("date_sort", "")
    awards_title2ds = {normalize(a.get("title", "")): a.get("date_sort", "")
                       for a in awards if isinstance(a, dict)}

    md = ex.render_news(news, awards)
    news_seq, awards_seq = [], []
    in_news = in_awards = False
    for line in md.splitlines():
        if line.startswith("> 最近动态"):
            in_news, in_awards = True, False
            continue
        if line.startswith("> 奖项"):
            in_news, in_awards = False, True
            continue
        m = re.match(r"- \*\*(.*?)\*\*：(.*)$", line)
        if in_news and m:
            news_seq.append(news_text2ds.get(normalize(m.group(2).strip()), ""))
        elif in_awards and line.startswith("- "):
            m2 = re.match(r"- (.+?)(?: — |$)", line)
            if m2:
                awards_seq.append(awards_title2ds.get(normalize(m2.group(1).strip()), ""))
    _seq_is_desc(news_seq, "export 成果总览 News", errors)
    _seq_is_desc(awards_seq, "export 成果总览 Awards", errors)

    pat_title2gd = {p.get("title", ""): p.get("grant_date", "")
                    for p in patents.get("patents", []) if isinstance(p, dict)}
    seq = []
    for line in ex.render_patents(patents).splitlines():
        if line.startswith("| ") and not line.startswith("| ---"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 3 and cols[0] in ("granted", "published"):
                seq.append(pat_title2gd.get(cols[1], ""))
    _seq_is_desc(seq, "export 专利清单 (grant_date)", errors)

    # 学术服务：按组（date 组按 date_sort 倒序；none 组不校验）
    group_order = []
    for section in service.get("sections", []) if isinstance(service, dict) else []:
        for group in section.get("groups", []):
            if group.get("sort") == SERVICE_NONE_SORT:
                continue
            by_text = {}
            for b in group.get("bullets", []):
                by_text[normalize(_entry_text(b))] = b.get("date_sort") if isinstance(b, dict) else ""
            group_order.append((group.get("title", ""), by_text))
    seqs = {i: [] for i in range(len(group_order))}
    cur = -1
    for line in ex.render_service(service).splitlines():
        if line.startswith("### "):
            title = line[4:].strip()
            cur = next((i for i, (t, _) in enumerate(group_order) if t == title), -1)
        elif cur >= 0 and line.startswith("- "):
            text = normalize(line[2:].strip())
            seqs[cur].append(group_order[cur][1].get(text, ""))
    for i, (title, _) in enumerate(group_order):
        _seq_is_desc(seqs[i], f"export 学术服务 / {title}", errors)


def check_consumer_cv_order(errors):
    """cv2tex.py 生成的 LaTeX 各节必须倒序（work/education startDate、publications 组内
    bib date、awards date、granted patents grant_date）。"""
    import json
    import cv2tex
    cv_path = Path(cv2tex.DEFAULT_CV)
    if not cv_path.exists():
        return
    cv = json.loads(cv_path.read_text(encoding="utf-8"))
    bib = cv2tex.parse_bib(str(cv2tex.DEFAULT_BIB))
    tex = cv2tex.render(cv, bib)

    def section_text(start):
        i = tex.find(start)
        if i < 0:
            return ""
        j = tex.find(r"\section*{", i + 1)
        return tex[i:j if j >= 0 else len(tex)]

    sec = section_text(r"\section*{Professional Experience}")
    _seq_is_desc(re.findall(r"\\textit\{(\d{4}-\d{2})[^}]*\}", sec),
                 "CV PDF Professional Experience (startDate)", errors)
    sec = section_text(r"\section*{Education}")
    _seq_is_desc(re.findall(r"\\textit\{(\d{4}-\d{2})[^}]*\}", sec),
                 "CV PDF Education (startDate)", errors)
    sec = section_text(r"\section*{Honors \& Awards}")
    _seq_is_desc(re.findall(r"\((\d{4}(?:-\d{2})?)\)", sec),
                 "CV PDF Honors & Awards (date)", errors)
    sec = section_text(r"\section*{Granted Patents}")
    _seq_is_desc(re.findall(r"Granted: ([\d-]+)", sec),
                 "CV PDF Granted Patents (grant_date)", errors)

    for heading in ("Representative Publications", "Other Publications", "Preprints", "Thesis"):
        i = tex.find("\\textbf{" + heading)
        if i < 0:
            continue
        j = tex.find("\\textbf{", i + 1)
        if j < 0:
            j = tex.find(r"\section*{", i + 1)
        if j < 0:
            j = len(tex)
        seq = re.findall(r"\((\d{4})\)\. ", tex[i:j])
        if seq:
            _seq_is_desc(seq, f"CV PDF {heading} (year)", errors)

    # Academic Services：date 块渲染为 join 一行，块内须按 date_sort 倒序
    sv_tex = section_text(r"\section*{Academic Services}")
    cv_svc = cv.get("service", {}) or {}
    for label, block in (("Journal Editorial Roles", "editorial"), ("Conference Program Committees", "program_committees"),
                         ("Conference Reviewer", "conference_reviewer"), ("Reviewer Recognition", "recognition")):
        items = [it for it in (cv_svc.get(block) or []) if isinstance(it, dict)]
        if not items:
            continue
        i = sv_tex.find("\\textbf{" + label)
        if i < 0:
            errors.append(f"CV PDF 缺 Academic Services 块: {label}")
            continue
        j = sv_tex.find("\\textbf{", i + 1)
        if j < 0:
            j = len(sv_tex)
        m = re.search(r"\\item\s+(.+?)\\end\{itemize\}", sv_tex[i:j], re.S)
        if not m:
            continue
        _verify_joined_service_line(items, m.group(1).strip(),
                                    f"CV PDF Academic Services / {label}", errors)


def check_cv_page_order(site_dir, errors):
    """/cv/ 页面渲染的 cv.json 列表必须倒序。"""
    cv_page = Path(site_dir) / "cv" / "index.html"
    cv_path = DATA / "cv.json"
    if not cv_page.exists() or not cv_path.exists():
        return
    import json
    cv = json.loads(cv_path.read_text(encoding="utf-8"))
    raw_html = cv_page.read_text(encoding="utf-8")

    # 按 <h1> 节切片，避免标题/日期撞到页面其它节（如 service 节里的 "ICML 2026 Silver Reviewer"）
    h1s = [(m.start(), html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip())
           for m in re.finditer(r"<h1[^>]*>(.*?)</h1>", raw_html, re.S)]

    def block(name):
        for i, (pos, hname) in enumerate(h1s):
            if name in hname:
                end = h1s[i + 1][0] if i + 1 < len(h1s) else len(raw_html)
                return normalize(raw_html[pos:end])
        return ""

    work_pairs = [(f"{w.get('startDate','')} – {w.get('endDate','')}", w.get("startDate", ""))
                  for w in cv.get("work", []) if w.get("startDate")]
    if work_pairs:
        check_rendering_order(work_pairs, block("Professional Experience"), "/cv/ work", errors)
    edu_pairs = [(f"{e.get('startDate','')} – {e.get('endDate','')}", e.get("startDate", ""))
                 for e in cv.get("education", []) if e.get("startDate")]
    if edu_pairs:
        check_rendering_order(edu_pairs, block("Education"), "/cv/ education", errors)
    aw_pairs = [(a.get("title", ""), a.get("date", ""))
                for a in cv.get("awards", []) if isinstance(a, dict)]
    if aw_pairs:
        check_rendering_order(aw_pairs, block("Honors & Awards"), "/cv/ awards", errors)
    # publications 各组：用 raw HTML 的 <strong>组标题</strong> 切片，避免普通词（如 thesis）在正文提前出现
    pub_groups = (("representative", "Representative Publications"), ("other", "Other Publications"),
                  ("preprint", "Preprints / Under Review"), ("thesis", "Thesis"))
    markers = [(g, f"<strong>{h2}</strong>") for g, h2 in pub_groups]
    for i, (g, marker) in enumerate(markers):
        start = raw_html.find(marker)
        if start < 0:
            continue
        end = raw_html.find(markers[i + 1][1], start + 1) if i + 1 < len(markers) else len(raw_html)
        if end < 0:
            end = len(raw_html)
        pub_block = normalize(raw_html[start:end])
        pairs = [(p.get("name", ""), str(p.get("year", "")))
                 for p in cv.get("publications", []) if p.get("group") == g and p.get("name")]
        if pairs:
            check_rendering_order(pairs, pub_block, f"/cv/ pubs/{g}", errors)

    # Academic Services：date 块 join 行内须按 date_sort 倒序
    svc_block = block("Academic Services")
    if svc_block:
        cv_svc = cv.get("service", {}) or {}
        page_heads = (("Journal Editorial Roles", "editorial"), ("Conference Program Committees", "program_committees"),
                      ("Conference Reviewer", "conference_reviewer"), ("Reviewer Recognition", "recognition"))
        for label, key in page_heads:
            items = [it for it in (cv_svc.get(key) or []) if isinstance(it, dict)]
            if not items:
                continue
            hi = svc_block.find(normalize(label))
            if hi < 0:
                errors.append(f"/cv/ 页缺 Academic Services 块: {label}")
                continue
            nxt = [x for x in (svc_block.find(normalize(h2)) for h2, _ in page_heads if h2 != label) if x > hi]
            seg = svc_block[hi:min(nxt) if nxt else len(svc_block)]
            bi = seg.find("- ")
            if bi < 0:
                continue
            joined = seg[bi + 2:].split("\n")[0].strip()
            _verify_joined_service_line(items, joined, f"/cv/ {label}", errors)


CV_HONORS_CATS = ("research", "reviewer", "academic", "mentorship")
_GENERIC_TOKENS = {"research", "media", "security", "impact", "international",
                   "contributions", "system", "open", "source", "community"}
_MEDIA_PERSONS = {"schneier", "anderson"}  # 背书以"被 X 赞扬"并入媒体串（B 期拆分后更新）


def _cv_service_date_map(cv):
    """cv.json service 的 date 块 → {normalize(name): date_sort}。"""
    m = {}
    for block in ("editorial", "program_committees", "conference_reviewer", "recognition"):
        for it in (cv.get("service", {}) or {}).get(block, []) or []:
            if isinstance(it, dict) and it.get("name"):
                m.setdefault(normalize(it["name"]), it.get("date_sort", ""))
    return m


def check_cv_yml_sync(awards, service, errors):
    """cv.json 与 yml 数据分流一致（error 模式）：
    - awards：research/reviewer/academic/mentorship → cv.json Honors & Awards（须存在，
      且 cv `date` == yml `date_sort`、`date_estimated` 标志一致）；industry/media → cv.json impacts；
    - service：yml date 组条目按**会议代号**比对（cv 措辞可不同，如 yml bullet 带全称、cv 只写代号），
      日期必须与 yml date_sort 一致（规则见 docs/update-workflow.md 第五节）。"""
    cv_path = DATA / "cv.json"
    if not cv_path.exists():
        return
    import json
    cv = json.loads(cv_path.read_text(encoding="utf-8"))
    cv_awards = cv.get("awards", []) or []
    impacts = cv.get("impacts", {}) or {}
    im_text = {k: " ".join(v or []) for k, v in impacts.items()}
    for a in awards:
        if not isinstance(a, dict):
            continue
        cat = a.get("category")
        at = tokens(a.get("title", ""))
        if cat in CV_HONORS_CATS:
            best = next((c for c in cv_awards
                         if normalize(a.get("title", "")) == normalize(c.get("title", ""))
                         or len(at & tokens(c.get("title", ""))) >= 2), None)
            if best is None:
                errors.append(f"cv.json Honors & Awards 缺 yml 条目[{cat}]: {a.get('title','')[:60]}")
            else:
                if (best.get("date") or "") != (a.get("date_sort") or ""):
                    errors.append(f"cv.json 条目日期与 yml date_sort 不一致: {a.get('title','')[:50]} "
                                  f"(cv {best.get('date','')} vs yml {a.get('date_sort','')})")
                if bool(best.get("date_estimated")) != bool(a.get("date_estimated")):
                    errors.append(f"cv.json 条目 date_estimated 与 yml 不一致: {a.get('title','')[:50]}")
        elif cat in ("industry", "media") and im_text.get(cat):
            key = at - _GENERIC_TOKENS
            covered = key and (key & tokens(im_text[cat])) or (cat == "media" and tokens(im_text[cat]) & _MEDIA_PERSONS)
            if key and not covered:
                errors.append(f"cv.json impacts.{cat} 未体现 yml 条目: {a.get('title','')[:60]}")

    cv_svc_map = _cv_service_date_map(cv)
    for section in service.get("sections", []) if isinstance(service, dict) else []:
        for group in section.get("groups", []):
            if group.get("sort") == SERVICE_NONE_SORT:
                continue  # 期刊审稿（alpha/none）等手工序组不在此比对范围
            for b in group.get("bullets", []):
                text = _entry_text(b)
                m = re.match(r"\*\*(.+?)\*\*", text)
                if not m:
                    continue
                code = normalize(m.group(1))
                ds = b.get("date_sort") if isinstance(b, dict) else ""
                if code not in cv_svc_map:
                    errors.append(f"cv.json service 缺 yml 服务条目（代号比对）: {code[:50]}")
                elif ds and cv_svc_map[code] != ds:
                    errors.append(f"cv.json service 条目日期与 yml 不一致: {code[:40]} "
                                  f"(cv {cv_svc_map[code]} vs yml {ds})")


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
    check_evidence_security(news, errors)
    check_file_refs(news, awards, service, patents, errors=errors)
    check_service_rendered(service, site_dir, errors)
    check_hardcoded_duplication(yml_values(news, awards, service, patents), ROOT / "_pages", errors)

    # ---- 日期字段存在性 + 渲染倒序 ----
    check_dates_present(news, service, awards, patents, errors)

    homepage = Path(site_dir) / "index.html"
    if homepage.exists():
        home_html = normalize(homepage.read_text(encoding="utf-8"))
        news_pairs = [
            (f"{i.get('date_display','')}: {i.get('text','')}", i.get("date_sort"))
            for i in news if isinstance(i, dict) and not i.get("commented")
        ]
        check_rendering_order(news_pairs, home_html, "首页 Recent News", errors)
        feat_pairs = []
        if isinstance(service, dict):
            for f in service.get("featured", []):
                feat_pairs.append((_entry_text(f), f.get("date_sort") if isinstance(f, dict) else None))
        check_rendering_order(feat_pairs, home_html, "首页 Professional Services", errors)
        aw_feat = [
            (a.get("title", ""), a.get("date_sort"))
            for a in awards if isinstance(a, dict) and a.get("featured")
        ]
        check_rendering_order(aw_feat, home_html, "首页 Awards", errors)

    activities = Path(site_dir) / "activities" / "index.html"
    if activities.exists():
        act_html = normalize(activities.read_text(encoding="utf-8"))
        for section in service.get("sections", []) if isinstance(service, dict) else []:
            for group in section.get("groups", []):
                if group.get("sort") == SERVICE_NONE_SORT:
                    continue
                pairs = [
                    (_entry_text(b), b.get("date_sort") if isinstance(b, dict) else None)
                    for b in group.get("bullets", [])
                ]
                check_rendering_order(pairs, act_html, f"/activities/ {group.get('title','')}", errors)

    awards_page = Path(site_dir) / "awards" / "index.html"
    if awards_page.exists():
        aw_html = normalize(awards_page.read_text(encoding="utf-8"))
        for cat in ("research", "reviewer", "academic", "mentorship", "industry", "media"):
            pairs = [
                (a.get("title", ""), a.get("date_sort"))
                for a in awards if isinstance(a, dict) and a.get("category") == cat
            ]
            if pairs:
                check_rendering_order(pairs, aw_html, f"/awards/ {cat}", errors)

    # ---- 消费方产物顺序（export_obsidian md / CV LaTeX / /cv/ 页面）----
    check_consumer_export_order(news, service, awards, patents, errors)
    check_consumer_cv_order(errors)
    check_cv_page_order(site_dir, errors)

    # ---- cv.json ↔ yml 分流一致性 ----
    check_cv_yml_sync(awards, service, errors)

    print(f"news: {len(news)} | awards: {len(awards)} | service sections: {len(service.get('sections', []))} | patents: {len(patents.get('patents', []))}")
    if errors:
        print(f"[FAIL] {len(errors)} 处不一致：")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("[OK] 一致性检查全部通过")


if __name__ == "__main__":
    main()
