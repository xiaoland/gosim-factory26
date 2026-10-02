> **实验当前已暂停。** 2026-10-02 20:48 CST，用户因 API 额度要求立即暂停所有实验；两个 baseline 原容器实际 Paused=true，controller T，不自动恢复。Console 服务可保持，但原生成容器只读执行需未暂停，暂停期间数据请求会明确报告暂停边界，不能为浏览自动 unpause。历史 producer running 字段只代表暂停前观测；实际暂停效果归 baseline 的 user-pause-20261002 原始回执。

# 当前实验接入修复

当前稳定根：`/Users/lanzhijiang/.local/share/factory26/exp-console/20261002-current-runs-reading`，service `5c80fa07-731a-4539-811b-1d8ca0f149d6`，HTTP PID99106，入口 8765。两当前 baseline 登记保留，旧 WSL 历史服务保留。

2026-10-02。当前范围为 Exp Console 正确显示并读取两组 I14 baseline GitHub 现场；不改变生成、模型配方、评测或实验资源。用户指出“exp console看到的正在运行的实验似乎不正确，也无法正常加载数据”，直接授权该范围修复；既有 Console 授权允许直接应用和重新部署。

旧 8765 是 Mac SSH 转发到 WSL 服务，manifest 只有七条历史登记，两组当前 baseline 未登记。五个旧现场返回具体错误 `ValueError: CLI 访问容器需要运行且未暂停`。旧 run.json 字段和启动时缓存不能代表当前 exp attempt 状态。旧服务、原 IDs、配置和材料保留为历史入口，不将旧 ID 指向新现场。

新服务在持有 experiment 及冻结 controller 的 Mac 长期目录准备。当前运行的 Braid 数据库、原生会话和工作树位于原生成容器 `/workspace/template` overlay，独立访问容器无法共享。采用显式 `runtime-readonly` 接入，核对冻结 exp attempt 的真实资源、完整容器 ID、StartedAt、owner labels、SSH endpoint、daemon ID 与容器内 Braid binary SHA-256。路径属于原容器 namespace，不登记虚构的宿主挂载。注册必须只读，所有对象写入、暂停/恢复和 access-start/stop 均拒绝；原 Unix 独立访问容器的已有合同保留。

只登记 `runs/iteration14/baseline-roots-20261002/active-bindings.json` 的有效两项：GLM Braid `20261002-110120-f5e81834` 和 Flash Braid `20261002-110738-65a19bd7`，排除未取得模型输出的设施失败。首页从对应 attempt 的生产者 observation 读取身份一致的状态、variant 和观测时间，并刷新访问错误；不从目录名字猜 running。

Python 编译及 TypeScript/Vite 构建通过，Vite 保留首页 chunk 超过 500 kB 提示。新服务已准备到 `/Users/lanzhijiang/.local/share/factory26/exp-console/20261002-current-runs`，service ID `95a2c8a7-d1d2-4b51-bf6e-266e3c83af42`。先在独立 8766 验证真实两组 HTTP 数据，成功后只关闭核对过的旧 Mac SSH 转发，再切换 8765。旧 WSL HTTP 原位保留，不安装自动重启。实际结果与切换身份待下方写入。

原始证据：`runs/braid-console-control/20261002-current-runs/`，包括旧 HTTP 错误、显式 registry、新服务 launch 与真实 HTTP 回包。没有设施测试、探针、测试评论、模型调用或实验暂停/恢复。主 Agent 独立浏览器采用新页面。


## 实际部署与独立采用

新服务在 8766 的两组 items/sessions 及 GLM 原文、代码 refs/workspace 全部真实 HTTP 200 后，核对旧转发 PID93554 的完整命令及 2026-10-01 18:33:26 出生时间，仅关闭该 Mac 转发。稳定服务于 2026-10-02T12:18:02Z 运行在原 8765，PID60312、instance `a6e925d3-6d10-441e-b45a-183b82ff2d10`。两当前 IDs 均 `writable=false`、`controllable=false`、无 access_error，producer 状态 running。切换及回包归 `deployment-switch.json` 和 `http-runs-8765.json`。旧 WSL HTTP 保留为历史服务，未终止、迁移或重指旧 ID。

主 Agent 独立 IAB 采用：首页显示两当前 baseline；Flash 的两个工作项、Issue 11 条评论、关联当前/历史会话与 provider 对话 50 条均可读；GLM 三工作项（基础 PR 已合并、REQ-1 PR 开放）、根会话三个 provider 及 idle 身份均可读，只读权限正确。没有重复浏览器验收。

20:06 CST 既有 monitor 曾出现 Flash 的 `docker --host ssh://sfp7-ws.localhost info --format '{{.ID}}'` 10 秒 TimeoutExpired，原时点 1790942791.679631，归 `flash-monitor-original-timeout.json`。20:16 同生产者观测已恢复，两当前 attempt running、无 observation_error；新服务真实 SSH Docker info/inspect 和 CLI 读取也成功。此为已恢复的采集瞬态失败，旧 running 不作失败轮的新证明，不改超时、不恢复或重试生成。

主线交接仅 e2e 声称已有实际状态；cleaner/reviewer 没有可用 Braid，均不登记。e2e 交接 expected SHA `63fdabce…` 与实际 `/workspace/submission/runtime/bin/braid` 及该 run 的 `work/bin/braid` SHA `e002edb848…` 不同，已保留 `e2e-binary-mismatch.json` / `e2e-binary-path-readback.json`，尚未登记。源 owner 正核对更正身份；不能从实际读回反推冻结身份。此处是交接身份门控，非 Console 读管道失败，两 baseline 服务不受影响。


## 20:43 CST：PR2 最新 provider 的 0 Turn 已解释并修复显示

用户指出 Flash PR2 成员 `01a0fc57-8cf1-71a0-bf72-3ca3db17fbcd` 最新 provider `01a0fc6f-8244-7991-a2f4-cc8cd7140fdb` 显示零 Turn。定向核对 CLI、原生材料、Pi 进程及真实数据库：旧 provider `01a0fc57-8d59-73c1-b292-2f289251d95f` 的唯一 Braid Turn 在 11:19:53Z 开始、11:46:01Z 正常 completed，error 为 null；当前不是“此前没执行”。此前 11:20:47Z 请求的 context reset 在旧 Turn 完成后于 11:46:04Z applied，真实 continuation 为 SQLite 数字 `0`，新 DB session `01a0fc6f-9009-77d3-a6c2-5819a24b5aca` 为 idle、resume_count 0、turns 空。新 native ID `01a0fc6f-8c0a-76f2-8348-d411935c74c9` 的 JSONL 未首次持久化，native-home 存在。

12:34:41Z，Pi PID18936、starttime8955202 仍活着，最新 managed-state 为 quiescent/input_readiness，isStreaming=false、isCompacting=false、pendingMessageCount=0。PR2 的 wake/event 全 consumed，没有 pending scheduler batch。store 的 apply_context_reset 按旧 Turn 的 durable terminal 决定是否 continuation：仅 interrupted/failed/unknown 会自动继续，本例 completed 不生成 wake。因此新 provider 是准备好等待新输入，不是已启动供应商请求后 stale；不改 Braid、不唤醒、不重启模型。advisor 独立采用该合同判断。旧 Turn 完成及 assistant 自报自检通过不作为应用交付或官方评测完成证据。

Console 原先把此准确路径 ENOENT 显示 HTTP400。已窄修复：只有 live、idle、明确空 turns、零偏移、该服务此前未读到此 provider 正文且精确目标文件 ENOENT，才返回 `not-persisted` 并保留路径不存在事实。size 为 null，不伪造空文件；其它错误、已有 Turn 或此前有正文的缺失仍报具体错误。前端明确“尚无持久化对话；等待首次轮次”，不把此状态当作正在生成。

Python 编译、TypeScript/Vite 构建通过。准备新稳定制品时两实际 exp/controller、容器出生身份、daemon 与 binary 门控均通过，先在 8766 实际读取当前 provider HTTP200/not-persisted，旧 provider HTTP200/50条原文，再切换 8765。新 service `5c80fa07-731a-4539-811b-1d8ca0f149d6`，根 `20261002-current-runs-reading`，PID99106，切换时点 1790944941.8739982。原 `20261002-current-runs` 的配置、active、journal 保全到新 history，原 manifest 退役；两 Braid ID、原生成容器、只读权限和旧 WSL 历史服务不变。主 Agent 独立 IAB 验收当前 provider idle/Turns0、两段等待文案可见，无 HTTP400。

证据统一归原目录 `flash-zero-turns/`：`sessions.json`、`native-readback.json`、`provider-lifecycle.json`、`provider-contact-schema.json`、`scheduling-readback.json`、`previous-provider-completion.json`、`context-reset-original-fields.json`、`new-provider-after.json`、`old-provider-after.json`、`new-provider-8765.json`、`deployment-reading-switch.json`。其中最初 scheduling 摘要误将 continuation 0 格式化为空串，补存的 `context-reset-original-fields.json` 保持实际原字段；不以错误摘要改变合同结论。核对 PR2 实际交付时另有两次 Docker inspect 10 秒瞬态超时，原 HTTP错误保留在 `pr2-published.json`，未据此修改超时或模型；本轮后续 prepare/HTTP 均成功。没有全量 rollout、探针、测试或额外采集循环。
