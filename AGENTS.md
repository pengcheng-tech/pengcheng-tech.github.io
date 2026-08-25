# 本仓库 Agent 工作规则

这是 Peng Cheng 的学术个人主页，Jekyll + AcademicPages，
部署在 GitHub Pages（pengcheng-tech.github.io）。

## 可以修改
- _data/*.yml, _data/cv.json
- _publications/*.md, publications.bib
- _pages/*.md 中的内容区块
- scripts/*

## 禁止修改（除非我明确点名）
- _config.yml, Gemfile, Gemfile.lock
- _sass/, assets/, _layouts/, _includes/
- images/, files/ 下的既有文件

## 每次改动必须走的流程
1. 从 master 切出分支：agent/<任务简称>
2. 改完运行 `bundle exec jekyll build`，构建失败就停下报告，
   不要自作主张去改配置或依赖来"修好"它
3. `gh pr create` 提 PR，绝不直接 push 到 master
4. 在 PR 描述里列出：改了哪些文件、新增/修改了哪些条目

## 内容风格
- 新闻日期格式：**Month YYYY**，倒序，最新在最上
- 我的名字在作者列表中加粗，通讯作者在名字后加 *
- 学生成果保留 "Congratulations to X on ..." 句式
- 不要改写我的 bio 和 Research Interests 段落，除非我要求

## 不确定时
宁可停下来问我，也不要猜。涉及职位、单位、头衔的表述一律先问。