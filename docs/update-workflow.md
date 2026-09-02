# 个人主页更新工作流（update-site）

本文件是主页内容更新的**唯一权威说明**。流程有变更时修改本文件并随 PR 提交（diff 可见、可追溯）。

## 一、核心：结构化输入

更新主页时按此模板提供信息（不用写完整句子，给字段即可）：

```
type: service | award | publication | patent
date: 2026-08
title: Program Committee Member, ACM CCS 2027
evidence: <来源与日期；不记录 URL / 邮件正文>
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
- **evidence**：以 `evidence:` 字段记录在对应条目的数据文件里（service / award 记在 news.yml 对应条目下）。模板只渲染具名字段（见 `_pages/about.md` / `_pages/activities.md`），`evidence` **不会被渲染**；用字段而非 YAML 注释，是为了让 `check_consistency.py` 等脚本能读取并校验。字段内容只记**来源与日期**（见第七节），不记录 URL / 邮件正文。

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
9. `git commit` 提交改动 —— **agent 到此为止**：不推送、不建 PR
10. 提交完成后直接输出**分支名**和**用户要执行的命令**（`git push -u origin <分支>` → `gh pr create`，描述见第六节）；不要尝试 push、不要检查 gh 认证、不要建议用户重新登录 gh。**每次回报的最后必须标注远端与本地提交差异**：用 `git ls-remote origin <分支>`（或 master）核实远端实际 tip，格式如「远端 `<sha>`，本地领先 N 个提交，需要 push」；本地与远端一致时也要明确写「远端 `<sha>`，本地与远端一致」。**不要假设"上一轮提示过 push 就等于用户推过了"**——PR #15 教训：4 个提交长期只存在于本地、从未上远端，用户按提示合并 PR 时合并的是旧提交，日期修正全部丢失。
11. 用户在本机终端推送分支、创建并合并 PR → GitHub Pages 自动部署上线
12. （可选）用户本地运行 `python3 scripts/export_obsidian.py` 刷新 Obsidian 只读视图

## 五、列表排序全局规则（时间倒序）

**所有页面上的内容列表一律按时间倒序**（最新在上），不依赖文件物理顺序。模板统一用
`sort: "date_sort" | reverse` 渲染；`check_consistency.py` 校验"条目必须有日期字段 + 渲染结果倒序"
（`check_consistency.py` 以 error 模式校验：缺日期字段或渲染非倒序即失败）。

- **统一日期字段 `date_sort: YYYY-MM`**：news / service / awards 的每个条目都有；同月多条的顺序**不受保证**
  （Liquid `sort | reverse` 对同键条目无稳定序），需要确定先后时请精确到不同月份。
  - news：**公告 / 得知消息的日期**（不一定是事件本身的日期——如奖项证书日期可能与 news 不同，此为设计、勿强行对齐；`sort: "date_sort" | reverse`，**与物理顺序无关**，旧新闻直接追加到文件末尾即可）
  - service：**受邀时间**（PC 当选 / 审稿邀请 / 客座编辑的日期）
  - awards：**事件实际发生日期**——以证书日期 / 比赛日期 / 授予日期为准，**不是公告日期**；与 news 的"得知 / 公告日期"是两个不同口径，二者不一致属正常，**勿互相对齐**
  - awards 的 **industry 类目**：`date_sort` 记**厂商作出认可的日期**（如厂商确认 / 致谢邮件的日期），**不是相关论文的发表日期**（SurrogatePrompt 曾误用 CCS 2024 发表月，已改为最早厂商认可 2023-09）
- **service.yml 结构**：`featured` / `bullets` 是对象数组（`{text, date_sort, date_estimated?}`）；组级 `sort: date`（默认，bullets 按 `date_sort` 倒序）| `none`（保持文件顺序——期刊审稿按刊物分量手工排序、Editorial 描述性 bullet 等）
- **估计日期标记 `date_estimated: true`**：历史条目查不到精确日期时，用年份默认值 `YYYY-01` 并加该标记，
  日后补到准确日期时需修正。**新增条目一律要求填写准确的受邀 / 获奖日期，不允许估计值**（结构化输入的
  `date` 字段必须为真实日期）。
- **例外 1 — Journal Reviewer（期刊审稿）**：期刊审稿是**持续性关系**而非一次性事件，该组**不参与时间倒序**：
  组级标记 `sort: none`，**按刊物分量手工排序**（如 Proceedings of the IEEE 在最前），**新增条目由用户指定插入位置、
  不做自动排序**；小节下加一行注明为持续性服务。
  理由：用"首次受邀年份"排序会让仍在活跃的服务显得陈旧；按刊物分量排序便于读者一眼看到顶级刊物。
  不同类数据用不同排序键（同类例子：patents 用 `grant_date` 而非 `date_sort`）。
- **例外 2 — patents（专利）**：无页面渲染、仅用于 CV；CV PDF 按 `grant_date` 倒序。

## 六、PR 描述固定模板

PR 描述必须包含以下三块，让审阅者扫一眼即可决定是否需要本地细看：

1. **改动摘要**：新增 / 修改了哪些条目（列出每条）
2. **渲染位置**：每条分别渲染在哪个页面的哪个小节（如：首页 Recent News、/awards/ 的 Research Awards & Competition Recognition、/activities/ 的 Program Committee Membership）
3. **`check_consistency.py` 输出**：[OK] 或失败明细

## 七、安全与措辞约束

- 本仓库公开：**任何本机绝对路径不得出现在被提交的文件里**；本机路径只放 `.env`（gitignored），脚本用 `os.getenv(...)` 读取。
- 含个人授权链接、收件地址的邮件内容一律**不得写入仓库文件**；`evidence` 字段只记**来源与日期**（如 `Invitation email from <会议名> Program Chairs, YYYY-MM-DD (via OpenReview)`），**不记录任何 URL**——原始邮件里的链接常含个人授权 token。
- 职位 / 头衔 / 委员会名称 / 奖项名次措辞：以官网或用户提供为准；不确定先问，不要猜。
- 不读写用户的 Obsidian 笔记（科研记录.md）；Obsidian 方向仅 `export_obsidian.py` 单向导出。
- 不向用户的坚果云同步目录写文件（本会话内）。
- 改动 `_pages/*.md` 的 Liquid 渲染节时，保证渲染 HTML 与重构前逐字一致（含加粗、链接、顺序）；验收用 diff 对比构建产物。
