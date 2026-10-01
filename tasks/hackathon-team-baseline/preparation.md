# 准备记录

2026-09-24 官网 `GET /api/competitions/hackathon` 当前可读，正式比赛 id 为 `hackathon`。
任务为 `hackathon--github`、`hackathon--sheet`，各 100 测试，共 200；API 标记 open、official。
原始详情与列表保存在 `runs/hackathon-team-baseline/discovery/`，当前详情 downloads 为 null；已下载需求在 WSL 保存，不能由此推断公开了测试。

WSL `/home/yyh/Development/factory26-official-local/platform-inputs` 现有 Lite、Web、Hackathon。
实际 Runner 目录为 `/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner`，不是文档示例的同级 runner。
Docker 镜像 `arcbench-local-submit:latest` 当前 ID `840105914e6e`；磁盘可用约 77 GB，观测时无运行中的容器。
旧最新 Braid 制品在 `factory26/runs/braid-usability-lite/20260924/boundary-fix`；其中 runtime 不含本轮新探索工具。
不覆盖另一会话的 `hackathon-runtime-{pi,codex}`、模型网关、生成产物或评分记录。

官方 LLM key 现存本机 `~/.config/factory26/llm.env`（仅记录路径）；远端项目 `.secrets` 当前只有另一会话的 models.env。
本任务不使用那个自购供应商网关，后续仅将官方 key 写到本任务需要的私有 env 文件。
Python 默认 HTTPS 证书链在本机读取模型列表时失败，改用现有 curl 的系统证书链；未关闭 TLS 校验。

官方 `https://api.arc-bench.com/v1/models` 使用已有 key 经 curl 返回 HTTP 200。
当前配方涉及的 `glm-5.3-flash`、`deepseek-v4-flash`、`kimi-k3`、`deepseek-v4-flash-vision-exp` 均在列表中；原始列表已保存。
这只确认目录和当前 key 的读取权限，尚不证明实际生成请求成功、可并发使用多个模型或官网容器外网可达。


本轮追加调查：当前前端 asset `https://arc-bench.com/assets/index-KN-S4Cyu.js` 已保存为 discovery/frontend-0.js；其中 official_evaluation/self_funded 的实际表单字段与临时 Key 说明见 design.md。
`/api/teams/me` 的 competition_budgets 当前为 Hackathon 初始 500、余额 500 CNY；只记额度，不归档无关的账户信息。
现有 competition.py 未处理 credential_mode；不能直接拿旧提交路径验证正式凭据行为。
WSL 需求目录按实际文件统计的尺寸与图片数量见 design.md；没有读取或调整隐藏测试。
