---
name: update-site
description: 更新本学术主页的内容（news / publications / awards / service / patents）并走完构建与 PR 流程。当用户以结构化输入提供新条目，或要求"更新主页/加一条新闻/收录论文/加奖项/加服务/加专利"时使用。
---

# update-site

维护本仓库（Jekyll + AcademicPages 学术主页）的内容更新工作流。数据源全部数据化，**网站只从数据文件渲染**。

## 数据模型（唯一真相源）

| 数据文件 | 内容 | 渲染位置 |
| --- | --- | --- |
| `_data/news.yml` | 新闻时间线（最新在最上，文件顺序即渲染顺序） | about.md `## Recent News`（Liquid）|
| `publications.bib` | 论文（唯一真相源） | 由 `scripts/bib2md.py --prune` 生成 `_publications/*.md` |
| `_data/service.yml` | 学术服务（PC/Editor/Reviewer/项目/指导） | about.md `## Professional Services`（Liquid）|
| `_data/awards.yml` | 奖项（**不上首页**，供未来 cv.json / 独立页） | 不渲染 |
| `_data/patents.yml` | 专利（**不上首页**；**本地保留、已 gitignore、绝不提交**——含私有申请号，仅个人备份与本地工具用） | 不渲染 |

`_data/news.yml` 条目字段：`date_display`（Month YYYY）、`date_sort`（YYYY-MM）、`text`（支持 **加粗**）、`links`（可选 label+url）、`type`（可选：service/award/publication）、`paper`（type=publication 时的 bib key）、`commented`（true 则按注释隐藏）。

## 用户输入模板（固定解析，不靠自然语言猜）

```
type: service | award | publication | patent
date: 2026-08
title: Program Committee Member, USENIX Security 2027
evidence: <URL 或说明>
files: <本机绝对路径，可选——用于复制证书等到 files/>
note: <补充要求，可选>
```

## 联动映射

| type | 更新 |
| --- | --- |
| service | `_data/news.yml`（加一条）+ `_data/service.yml`（加到对应 section）|
| award | `_data/news.yml` + `_data/awards.yml`（**不渲染，仅数据**）|
| publication | `_data/news.yml` + `publications.bib`（新增条目）+ 重跑 `scripts/bib2md.py --prune` |
| patent | `_data/patents.yml`（**绝不进 news**）|

## 执行流程（每次必须完整走完）

1. `git checkout master && git pull`，再从 master 切分支：`git checkout -b agent/<任务名>`
2. 按映射更新数据文件；`files:` 里的本机文件复制进 `files/` 并重命名（**文件名不含本机路径信息**）
3. 重新生成（如涉及）：`python3 scripts/bib2md.py --prune`
4. `bundle exec jekyll build` —— 失败立即停下报告，**不得改 Gemfile 或 _config.yml**
5. `python3 scripts/check_consistency.py` —— 失败立即停下报告
6. 提交、推送、`gh pr create`（base master）；PR 描述列出改动文件与新增条目

## 措辞与安全约束（必须遵守）

- 职位/头衔/委员会名称/奖项名次措辞：**官网或用户提供的信息为准**；不确定一律先问，不要猜。
- 本仓库是公开仓库：**任何本机绝对路径不得出现在被提交的文件里**（skill、脚本、AGENTS.md、数据文件等一律禁止）。本机路径只放在 `.env`（已 gitignore），脚本用 `os.getenv(...)` 读取；`scripts/export_obsidian.py` 使用 `OBSIDIAN_SYNC_DIR`。
- **绝不读写用户的 Obsidian 笔记**（如 科研记录.md）。Obsidian 方向是单向导出：`scripts/export_obsidian.py` 生成只读视图到 `$OBSIDIAN_SYNC_DIR/_自动同步/`（含"自动生成请勿手工编辑"横幅），由用户自行运行。
- **不要向用户的坚果云同步目录写任何文件**（并发写会产生同步冲突副本）——本会话内不得把文件写到该目录。
- 改动 `_pages/about.md` 的 Liquid 渲染节时，保证渲染 HTML 与重构前逐字一致（含加粗、链接、顺序）；验收用 `diff` 对比构建产物。
- patents 数据只进 `_data/patents.yml`，不上首页。
