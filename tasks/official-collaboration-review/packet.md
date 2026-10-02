# 官网协作记录人工复审

用户授权将上一批官网 GitHub/Sheet 的 Issue、PR 重建成 GitHub-like HTML，并继续过程分析、浏览器工具分析、产品复审；本单元只生成复审材料，不修改原工作区或 Braid。
来源是 runs/e20260928-completed-replay/{github,sheet}/source-workspace.zip，分别对应生成 run 435b79927a47、bd7ac1b232ba，不把后来的评分 run 当作生成会话。
展示原始数据库保存的最终正文、评论、回复、可见性/解决状态、活动、指派和 PR 关系；不编造未保存的正文历史或 Git diff。投递回执不等于模型已读取。
产物 runs/official-collaboration-review/index.html，离线单文件；生成入口 render.py。原始文本保存在伴随 data.json，可复查展示的来源。

本次边界澄清：检查辅助脚本允许作为 Agent Skill 资产提供；Harness 不得将其直接写入生成应用 package.json/src/scripts。原撤回方案仍不恢复为应用写入。

已生成离线HTML：GitHub 16对象/284评论，Sheet 17对象/216评论。浏览器工具拒绝访问本地file URL，未绕过策略，因此视觉交互复核尚未完成；交付可下载HTML供用户打开。
