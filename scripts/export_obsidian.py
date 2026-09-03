#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_obsidian.py — Generate a read-only Obsidian view of the site data.

Direction: repo -> Obsidian. The repo files (_data/*.yml, publications.bib)
are the single source of truth; this script only *exports* a read-only
snapshot into $OBSIDIAN_SYNC_DIR/_自动同步/. It never reads or writes the
user's own research notes (科研记录.md).

Ordering follows the global rule (docs/update-workflow.md §5): every list is
rendered newest-first by `date_sort` (news / awards / service date-groups by
`date_sort`, service `sort: none` groups in file order, patents by
`grant_date`). check_consistency.py verifies this output order.

Generated files (all start with a "generated, do not edit" banner):
  _自动同步/成果总览.md    — news timeline + awards + publications overview
  _自动同步/专利清单.md    — patent list from _data/patents.yml
  _自动同步/学术服务.md    — academic service sections from _data/service.yml

The target directory comes from the OBSIDIAN_SYNC_DIR environment variable
(.env at the repo root may set it; the variable wins). No machine-specific
paths are hard-coded in this repository.

Usage:
  export OBSIDIAN_SYNC_DIR=/path/to/obsidian/vault
  python3 scripts/export_obsidian.py --dry-run
  python3 scripts/export_obsidian.py
"""

import argparse
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
AUTO_DIR = "_自动同步"

SERVICE_NONE_SORT = "none"  # 组级标记：保持文件顺序（期刊审稿按分量手工排序、描述性 bullet）

BANNER = (
    "> 本文件由 scripts/export_obsidian.py 自动生成，请勿手工编辑。\n"
    "> 修改请到仓库根目录的 _data/*.yml 或 publications.bib，然后重新运行该脚本。\n"
)


def load_env(path: Path):
    """Tiny .env loader: KEY=VALUE lines; existing env vars win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_yaml(name):
    path = ROOT / "_data" / name
    if not path.exists():
        return {}  # optional data file (e.g. gitignored patents.yml) may be absent
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def strip_md(text):
    return re.sub(r"\*\*|__", "", str(text or ""))


def _dated_desc(entries, key="date_sort"):
    """稳定倒序：按 key 降序；缺 key / 空值的条目沉底（保持文件内相对顺序）。"""
    def sortkey(e):
        if not isinstance(e, dict):
            return ""
        v = e.get(key)
        return str(v) if v else ""
    return sorted(entries, key=sortkey, reverse=True)


def _group_bullets_ordered(group):
    """与 /activities/ 渲染一致：`sort: none` 组保持文件顺序，其余按 date_sort 倒序。"""
    bullets = group.get("bullets", [])
    if group.get("sort") == SERVICE_NONE_SORT:
        return bullets
    return _dated_desc(bullets)


def awards():
    return load_yaml("awards.yml") or []


def render_news(news, awards_list=None):
    lines = ["# 成果总览", "", "> 最近动态（News）", ""]
    for item in _dated_desc([i for i in news if not (isinstance(i, dict) and i.get("commented"))]):
        lines.append(f"- **{item.get('date_display','')}**：{strip_md(item.get('text',''))}")
    lines.append("")
    lines.append("> 奖项（Awards，不展示在首页，仅存档）")
    lines.append("")
    for a in _dated_desc(awards_list if awards_list is not None else (awards() or [])):
        parts = [strip_md(a.get("title", ""))]
        if a.get("event"):
            parts.append(a["event"])
        if a.get("year"):
            parts.append(str(a["year"]))
        if a.get("detail"):
            parts.append(a["detail"])
        lines.append(f"- {' — '.join(parts)}")
    return "\n".join(lines) + "\n"


def render_patents(patents):
    lines = ["# 专利清单", ""]
    items = _dated_desc((patents.get("patents", []) or []), key="grant_date")
    if not items:
        lines.append("_（暂无条目——通过结构化输入 type: patent 添加，或手工编辑 _data/patents.yml）_")
        lines.append("")
        return "\n".join(lines)
    lines.append("| 状态 | 专利名称 | 申请号 | 授权/公布号 | 日期 | 排名 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for p in items:
        lines.append(
            f"| {p.get('status','')} | {p.get('title','')} | {p.get('number','')} | "
            f"{p.get('grant_number','')} | {p.get('grant_date','')} | {p.get('rank','')} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_service(service):
    lines = ["# 学术服务", ""]
    for section in service.get("sections", []):
        lines.append(f"## {section.get('heading','')}")
        lines.append("")
        for group in section.get("groups", []):
            lines.append(f"### {group.get('title','')}")
            lines.append("")
            for b in _group_bullets_ordered(group):
                text = b.get("text") if isinstance(b, dict) else b
                lines.append(f"- {strip_md(text)}")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print target paths and preview without writing")
    args = ap.parse_args()

    load_env(ROOT / ".env")
    target = os.getenv("OBSIDIAN_SYNC_DIR")
    if not target:
        print("[error] OBSIDIAN_SYNC_DIR 未设置（可在仓库根目录 .env 中配置，参见 .env.example）", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(target) / AUTO_DIR
    files = {
        "成果总览.md": render_news(load_yaml("news.yml") or []),
        "专利清单.md": render_patents(load_yaml("patents.yml")),
        "学术服务.md": render_service(load_yaml("service.yml")),
    }

    for name, body in files.items():
        content = BANNER + body
        path = out_dir / name
        if args.dry_run:
            print(f"[dry-run] 将写入 {path}（{len(content)} 字符）")
            print(content[:300].rstrip(), "…" if len(content) > 300 else "")
            print()
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"[written] {path}")

    if not args.dry_run:
        print(f"[done] 已生成 {len(files)} 个文件到 {out_dir}")


if __name__ == "__main__":
    main()
