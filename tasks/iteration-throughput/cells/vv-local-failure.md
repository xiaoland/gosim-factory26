# V&V/BookStack 本地生成中断

WSL run `20260923-085057-3199c9bc` 使用冻结包 SHA256 `485f70fcb58954b362f13099fc671411393b2acdb339bc5edc638a2179377a00`。它停在生成阶段，未交付应用，未执行 Playwright，因此没有 benchmark 分数。证据在 WSL `runs/local/iteration-throughput-boundary/pi-team-vv-bookstack/evidence/` 与保留的 `/tmp/factory26-4575vfl_/braid-state/`。

Issue agent 创建 PR #1 时显式 `--assignee glm`，覆盖默认的 `pi-deepseek-fast`，并直接在 PR 工作树写文件；PR agent 也在同一工作树执行。PR agent 的 npm 安装／构建工具调用达到 300 秒超时，此后连续收到模型 `Connection error`，既未提交也未 `pr ready`。最后 Issue/PR 均为 OPEN、`active_turns=0`、无待执行事件；Braid 报“根 Issue OPEN 且无后续可执行工作”是终态描述，没有证据表明调度器丢了正常的活跃 turn。

旧 PR 工作树还有未提交的 frontend/backend，但 `ready_commit=null`。Braid 的 `pr edit` 和 `pr comment` 都要求本次 dispatch 的新 `--writer-turn`，现有 CLI 没有独立 dispatch/resume 入口；再次运行 `braid local` 不会凭空产生新 turn。旧 package runner 对未交付 run 也会重新采样，故当前没有受支持的原地恢复路径。不要将手工改状态或重新采样后的结果混成同一 run。

同一冻结 ZIP 的独立无人干预重试在 WSL `runs/local/iteration-throughput-boundary/pi-team-vv-bookstack-retry-1/` 也以 `generation_failed` 结束，Braid 顶层消息相同，仍无评分。重试里 Issue 已正常分配，但最初八次 provider 调用全部 `Connection error.`，零工具调用；原 run 则在约 50 分钟正常工作后出现同类错误。后续独立网络探针确认 WSL 的自动 DNS `172.29.144.1` 无响应，本机模型 API 正常；临时修复及流式请求 HTTP 200 证据见[环境 cell](environment.md)。这支持两次由 WSL 解析故障触发，而非 ZIP 确定性缺陷。DNS 修复后，第二次干净重跑位于 `runs/local/iteration-throughput-boundary/pi-team-vv-bookstack-dns-retry-2/`。
