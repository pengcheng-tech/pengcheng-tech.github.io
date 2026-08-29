# 个人主页更新工作流（update-site）

本文件是主页内容更新的**唯一权威说明**。流程有变更时修改本文件并随 PR 提交（diff 可见、可追溯）。

## 一、核心：结构化输入

更新主页时按此模板提供信息（不用写完整句子，给字段即可）：

```
type: service | award | publication | patent
date: 2026-08
title: Program Committee Member, ACM CCS 2027
evidence: <官网链接 或 说明>
files: <本机文件绝对路径，可选——证书/图等我帮你复制进 files/>
note: <补充要求，可选>
```

## 二、四类信息的联动映射

| type | 更新文件 | 渲染位置 |
|---|---|---|
| `service`（当选 PC / 受邀审稿 / 客座编辑）| `_data/news.yml` + `_data/service.yml` | 首页新闻 + /activities/ |
| `award`（竞赛名次 / 获奖）| `_data/news.yml` + `_data/awards.yml` | 首页新闻 + 首页 Awards 精选（featured）+ /awards/ |
| `publication`（论文接收）| `_data/news.yml` + `publications.bib` + 重跑 bib2md | 首页新闻 + /publications/ |
| `patent`（专利）| `_data/patents.yml`（**已纳入版本控制**）| **不进新闻、不上首页**，仅出现在 CV |

- **award 有意不进奖项页**（如荣誉会员 CCF Senior Member）：加 `awards_entry: false`，保留 `type: award` 约束但不要求 awards.yml 有对应项；不要靠删除 type 绕过检查。
- **patent**：`patents.yml` 在版本控制中（26 条，`.gitignore` 无排除）；数据只进该文件，绝不进 news，不上首页，仅 `scripts/cv2tex.py` 生成 CV 时使用。

## 三、纯文字 vs 结构化（标准写死，不靠临场判断）

- **只要这条信息将来可能出现在 CV 上**（论文、奖项、学术服务、专利、项目、职务、荣誉等），**一律走结构化输入**。
- **纯文字只用于真正一次性、不进 CV 的事项**：受邀讲座、活动参与、纯日常公告等。
- 判断标准以此为准，不依赖临场问答。

## 四、执行流程（每次必须完整走完）

1. 解析结构化输入（type / date / title / evidence / files / note）
2. 查联动映射，确定要改的数据文件
3. `git checkout master && git pull` → 切分支 `agent/<任务名>`
4. 更新数据文件：
   - `news.yml` **追加**即可（**位置无关**——模板按 `date_sort` 倒序渲染，见第五节）
   - `service.yml` / `awards.yml` / `publications.bib` 对应位置
5. `files:` 里的本机文件 → 复制进 `files/` 并重命名（文件名不含本机路径）
6. 如涉及论文：`python3 scripts/bib2md.py --prune`
7. `bundle exec jekyll build` —— 失败立即停下报告（不改 Gemfile / _config.yml）
8. `python3 scripts/check_consistency.py` —— 失败立即停下报告
9. 提交 → 推送 → `gh pr create`（描述见第六节）
10. 用户合并 PR → GitHub Pages 自动部署上线
11. （可选）用户本地运行 `python3 scripts/export_obsidian.py` 刷新 Obsidian 只读视图

## 五、news 排序保证

Recent News 由模板 `site.data.news | sort: "date_sort" | reverse` 渲染，**与 news.yml 物理顺序无关**。
补录几个月前的旧新闻直接追加到文件末尾即可，会自动按 `date_sort` 排到正确位置。
（相同 `date_sort` 的条目保持文件内相对顺序——稳定排序。）

## 六、PR 描述固定模板

PR 描述必须包含以下三块，让审阅者扫一眼即可决定是否需要本地细看：

1. **改动摘要**：新增 / 修改了哪些条目（列出每条）
2. **渲染位置**：每条分别渲染在哪个页面的哪个小节（如：首页 Recent News、/awards/ 的 Research Awards & Competition Recognition、/activities/ 的 Program Committee Membership）
3. **`check_consistency.py` 输出**：[OK] 或失败明细

## 七、安全与措辞约束

- 本仓库公开：**任何本机绝对路径不得出现在被提交的文件里**；本机路径只放 `.env`（gitignored），脚本用 `os.getenv(...)` 读取。
- 职位 / 头衔 / 委员会名称 / 奖项名次措辞：以官网或用户提供为准；不确定先问，不要猜。
- 不读写用户的 Obsidian 笔记（科研记录.md）；Obsidian 方向仅 `export_obsidian.py` 单向导出。
- 不向用户的坚果云同步目录写文件（本会话内）。
- 改动 `_pages/*.md` 的 Liquid 渲染节时，保证渲染 HTML 与重构前逐字一致（含加粗、链接、顺序）；验收用 diff 对比构建产物。
