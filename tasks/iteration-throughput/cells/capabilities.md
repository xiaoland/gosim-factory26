# 能力装配预演

状态：Stage 3 能力装配已实现并通过静态与物化检查；真实模型资格仍受比赛网关 429 阻断，Linux ZIP 由集成阶段构建确认。

## Implementation result（2026-09-22）

- 活动配置已收敛为 `pi-team-deepseek`、`pi-team-glm`、`pi-team-mixed`、`pi-team-vv` 四个 `variant.json`；旧 preset、generalist、verification 与 reviewer 配置已退出源码活动面，历史 runs 未改写。variant 的默认值使用公开 login，resolver 将其唯一映射为 Braid request 所需的内部 profile ID。
- 两份 profile 显式拥有 `assignee_login`、`assignee_description`、core、text provider、model、reasoning、instructions、skills、CLI、五个 native role、空 MCP 与 Braid context 字节策略。公开 description 由 resolver 校验 GitHub 式 login、单行与 240-byte 上限，并拒绝内部配置词。
- 五个 role 都显式声明 provider、model、reasoning、tools、skills、MCP、instructions 和 fresh context。`explorer`/`executor` 使用 `deepseek-v4-flash`，`browser-operator`/`vision` 使用独立视觉 provider 的 `deepseek-v4-flash-vision-exp`，`specialist` 使用 `kimi-k3`；没有 reviewer 或隐式继承能力。
- `scripts/profiles.py` 是唯一 resolver。它验证实际 consumer、读取 canonical SVC bytes，并记录每份消费材料的 SHA-256。`pi-team-vv` 只额外携带 `methods/design/test.md` 与 `verification/index.md` 的原文和冻结 hash；`native_profiles.py` 只物化 effective contract，并把 V&V 原文追加到 Braid Agent user instructions。
- 文本与视觉 endpoint/key 已分离：Pi 模板生成 `factory26`/`FACTORY26_API_KEY` 和 `factory26-visual`/`FACTORY26_VISUAL_API_KEY`；没有视觉 endpoint 时后者明确回退到同一文本 endpoint/key。这是路由/凭据命名分离，不是账户 quota 隔离或 Harness 的额度分配。公开 assignee 字段直接进入 Braid profile，`display_name` 仅保留内部诊断 ID。
- `package_agent.py --variant ...` 把完整 harness、所选 variant、effective config、material hashes 和 source snapshot 写入同一 ZIP；manifest 新增 `capabilities.{variant,effective_digest,materials}`。Docker runtime 改为按 frozen npm lock 安装 Pi、Codex、pi-subagents、agent-browser，并预装 Chromium 与 Linux 依赖；四个 variant 复用同一 Docker layer cache。
- 运行时 `harness/AGENTS.md` 现在只提供 SVC semantic index、Task Packet 与 Verification 触发；主 instructions 只描述 Issue、PR、comment/reply、公开 assignee 和原生角色，不再暴露 profile/preset/variant/model/provider/digest/session。

验证：`make test` 共 124 项 Python 检查通过、1 项按既有 Linux 条件跳过，Pi lifecycle 检查通过；四 variant 均可解析，mixed/V&V delta、canonical hash、公开身份、五 role、text/visual 路由、Braid `issue/pr` request schema 和 material manifest 均有直接断言。未执行付费模型调用或外部写入。

剩余 gate：当前 catalog 对目标模型保留 `gateway_verified: false`，不能把 429 后的静态描述报告为 tool-call/reasoning/image 资格；Linux amd64 ZIP 仍需由集成阶段在 `arcbox-win` 实际构建并运行无模型资格，特别确认 Chromium 动态库与包内 runtime 路径。

## Observed

### 当前装配链

- `scripts/profiles.py:33-89` 先读取 `variants/<variant>/preset.json`，强制其只拥有 `profiles` 与 `defaults`，再展开 `harness/profiles/*.json`、`harness/subagents/*.json`、skills 和模型 catalog。它把 `reasoning` 限死为 `high`，把 `mcp` 限死为空，并生成 `effective_digest`。
- 当前有效结果为 `profiles`（内部 profile ID → `profile`、`roles`、`skills`、`models`、`common`、provider、Pi lifecycle）+ `defaults` + provider；没有公开 `login`/`description`、variant 方法装配或 canonical SVC 内容 hash。
- `scripts/native_profiles.py:95-98` 将 `display_name` 写成内部 profile ID，`context_soft_ratio=.8` 与 `context_hard_bytes=1000000` 在脚本硬编码；角色实际从各 `harness/subagents/*.json` 展开，Pi 入口通过 `factory-subagent-lifecycle.ts` 接入。
- `scripts/factory.py` 的旧 resolver 接缝曾把 shared-config 投影为 Braid request；当前独立 variant 直接持有运行材料，`scripts/package_agent.py` 只打包所选目录。
- 当前配置不是目标矩阵：`pi-generalist`、`codex-generalist` 是单 profile；`pi-team` 是 K3 coordinator + GLM UI + K2.7 app；`pi-verification` 另带 reviewer。四个 `preset.json` 都是一对一引用或简单列表，没有独立行为消费者。
- 当前 catalog 只含 `kimi-k3`、`kimi-k2.7-code`、`glm-5.3-flash`；目标 `deepseek-v4-flash` 与 `deepseek-v4-flash-vision-exp` 尚未进入 catalog。当前 role 文件也仍是 Kimi/GLM 组合，不能只改 profile model 字符串假装原生 role 已可用。
- `tests/test_profiles.py` 仍断言旧四 variant、preset 数量与 reviewer 形态；它是迁移时必须同步的边界检查，不是新合同的证据。

### SVC 事实

冻结 SVC source revision 为 `sources/svc/corpus@393b9352fae1e8b22d86b28a65ff2f7ded267a38`，工作树 clean。canonical 路径和当前 hash 为：

| 路径 | SHA-256 |
| --- | --- |
| `index.md` | `b79cca470c82f26fcf4504519988a2a14736099f485e7320b668ac93cfd67597` |
| `methods/design/test.md` | `bf80281aad0dae8b4c020ea2f9e2d214b6511b339f3821e80b879f5d7c3fadbbd` |
| `verification/index.md` | `2ffeb3b9e67f946cafc475ea2abd667caad0493a8102b862dfdd887537223381` |

`harness/AGENTS.md` 只有两行 `svc lookup` 导航；`svc-wiring-design.md` 的入口草案已明确 Task Packet、按需 Working Methods 和 Verification 的触发，但尚未接入。canonical 正文的 owner 是 SVC Corpus；Factory 只能冻结 revision、选择路径并注入，不复制正文。

## Effective schema 草图

删除 `preset` 概念后，variant 文件直接表达组合；profile/role/skill/catalog 各自保留唯一 owner。下面是建议的内部解析形状，字段名用于锁定责任，最终 CLI 名称可在实现前 handshake 时冻结：

```json
{
  "schema_version": 2,
  "variant": "pi-team-mixed",
  "profiles": [
    {
      "id": "pi-glm-fast",
      "login": "glm",
      "description": "通用需求理解、设计、实现与整合；适合低成本完整工作项。",
      "core": "pi",
      "model": "glm-5.3-flash",
      "reasoning": {"request_field": "reasoning_effort", "value": "high"},
      "instructions": ["harness/instructions/main.md"],
      "skills": ["ponytail", "impeccable"],
      "mcp": [],
      "native_roles": ["explorer", "executor", "browser-operator", "vision", "specialist"],
      "context": {"soft_ratio": 0.8, "hard_bytes": 1000000}
    }
  ],
  "defaults": {"issue": "glm", "pr": "deepseek"},
  "svc": {
    "source_revision": "393b9352fae1e8b22d86b28a65ff2f7ded267a38",
    "index": "index.md",
    "preload": []
  },
  "provider": {"id": "factory26", "base_url": "https://api.arc-bench.com/v1"},
  "effective_digest": "sha256(...)"
}
```

`pi-team-vv` 只把 `svc.preload` 变为 `["methods/design/test.md", "verification/index.md"]`，并记录两路径 hash；其 profiles、defaults、provider、native roles、skills、MCP 和 context 必须与 `pi-team-mixed` 相同。解析后的内部结构可以保留 `id` 供 Harness/Braid 映射，但运行时对象、Context、初始 instructions 和 assignee 目录只能投影 `login`、`description` 与可观察能力，不能泄漏 profile/preset/model/provider/digest/session 字段。

### Owner 表

| 内容 | 唯一 owner | 消费者 |
| --- | --- | --- |
| variant 的 profile refs、公开 login/description、Issue/PR 默认 assignee、SVC 路径选择 | `variants/<variant>/variant.json` | `scripts/profiles.py`、batch/controller |
| profile 的 core/model/reasoning/instructions、skills/MCP/native role refs、context policy | `harness/profiles/<profile>.json` | resolver、native materializer |
| role 的 model/reasoning/tools/skills/MCP/instructions | `harness/subagents/<role>.json` | `native_profiles.py`、Pi/Codex native core |
| skill 正文与来源材料 | `harness/skills/<skill>/` | profile/role materializer |
| 模型 wire descriptor、输入模态、context/maxTokens、reasoning 映射 | `harness/models.json` | resolver、native materializer、静态资格检查 |
| SVC 入口导航 | `harness/AGENTS.md` | 所有 runtime Agent |
| canonical SVC 正文 | `sources/svc/corpus/` | SVC owner；Factory 只按 frozen revision/path 注入 |
| effective 展开、digest、binding 与 Braid request | `scripts/profiles.py` + `scripts/native_profiles.py` | `scripts/factory.py` |
| package 内的 variant/material manifest | `scripts/package_agent.py` | official runner / hosted snapshot |
| run matrix、venue、task、并发和 package hash | controller/实验 manifest owner | `scripts/batch.py` 与 controller；本 Cell 不改活动配置 |

## 四 variant effective 差异

四组都使用 Pi、同一冻结 SVC source、同一 role 集合、同一 browser/vision model、同一 skills/MCP policy 和同一 package entry；只有下表字段变化：

| variant | profile refs | 默认 Issue | 默认 PR | SVC preload |
| --- | --- | --- | --- | --- |
| `pi-team-deepseek` | `pi-deepseek-fast` | `deepseek` | `deepseek` | `[]`，仅 semantic index 按需读取 |
| `pi-team-glm` | `pi-glm-fast` | `glm` | `glm` | `[]`，仅 semantic index 按需读取 |
| `pi-team-mixed` | `pi-glm-fast`, `pi-deepseek-fast` | `glm` | `deepseek` | `[]`，仅 semantic index 按需读取 |
| `pi-team-vv` | 与 mixed 完全相同 | `glm` | `deepseek` | `methods/design/test.md`, `verification/index.md` |

profile 建议：两个 Braid profile 都持有 `ponytail`、`impeccable` 的按需能力（是否保留两者以实际装配消费者为准），MCP 为空；五个 Pi native roles 为 `explorer`、`executor`、`browser-operator`、`vision`、`specialist`。`explorer`/`executor` 用 `deepseek-v4-flash`，`browser-operator`/`vision` 用 `deepseek-v4-flash-vision-exp`，`specialist` 用 `kimi-k3`；每个 role 的 tools、skills、MCP、context 和 reasoning 由 role 文件显式给出，不能由父 profile 猜测。若模型 spike 未通过，整组标记接口不成立，不静默降级。

## 模型接口 spike 证据

### 本次最小调用

使用 `~/.config/factory26/llm.env` 中既有 key，未打印、未写入仓库。请求仅到 `POST https://api.arc-bench.com/v1/chat/completions`，未创建应用、未提交 Competition、未启动 hosted run。脱敏原始材料在仓库外 `/tmp/factory26-capability-spike-20260922/`，其中 request/response/headers 文件不应进入 git。

文本请求形状：`model`、单条 string `messages`、一个 JSON Schema function tool、强制 `tool_choice`、`reasoning_effort:"high"`、`stream:false`。`deepseek-v4-flash` 与 `glm-5.3-flash` 均返回 HTTP `429`，响应 schema 为 `{error:{code,message,param,type},traceId}`；`type=insufficient_quota`，message 为 `Free allocated quota exceeded.`，没有 `choices`、`usage` 或 `cost`。因此当前不能把两者的 tool-call、reasoning 字段判为通过；失败归属为比赛网关余额/免费额度，尚不能归给请求 dialect、模型能力或 Factory adapter。

视觉请求同样尝试了本地 `favicon.png` 的 data URL 内容块：`content:[{type:"text",...},{type:"image_url",image_url:{url:"data:image/png;base64,..."}}]`，并带 `reasoning_effort:"high"`、`stream:false`；也返回同一 HTTP `429`，无 usage/cost。该次仅证明额度已阻断，不能重写既有视觉证据。

### 配额恢复后的最小资格重验（2026-09-22）

三模型资格探针已在 `runs/qualification/models/` 与 `runs/qualification/models-vision-auto/` 保存脱敏 request/response。`deepseek-v4-flash` 与 `glm-5.3-flash` 均 HTTP 200，强制 `lookup` 的参数分别为 `{"q":"ping","limit":1}`，且 response 含 `reasoning_content`；二者沿用先前已通过结果，没有重跑。视觉请求第一次在 HTTP 400 返回 `Thinking mode does not support this tool_choice`，证据保留在 `runs/qualification/models/`；provider 只有在消费者显式设置 `options.toolChoice` 时才发送 `tool_choice`，而当前消费者没有这个要求。因此第二次仅移除视觉请求的 named `tool_choice`，保持同一模型、图片、`reasoning_effort:"high"`、`stream:false`、`max_tokens:2048` 和 `observe` 提示，未换模型或降低 thinking，结果 HTTP 200、`finish_reason:"tool_calls"`、`observe({"color":"red"})`、含 `reasoning_content`，usage total 554。当前三模型最小能力资格成立；视觉边界是按消费者实际协议不强制 named `tool_choice`。

### 可复用既有证据

- `runs/20260920-141339-6138c072/native/*.jsonl` 记录过实际 `deepseek-v4-flash-vision-exp` Pi 调用：请求经 `api:"openai-completions"`，响应归一化为 `stopReason:"toolUse"`、`rawStopReason:"tool_calls"`，assistant content 含 `thinking` 与 `toolCall`；usage keys 为 `input/output/cacheRead/cacheWrite/reasoning/totalTokens/cost`。这是 Pi 归一化消息证据，不是裸 HTTP response 的完整字段。
- `tasks/multi-agent-integration/cells/capabilities-ready.md` 记录同一能力场景的 `image:true`、executor 和 browser operator 实际运行；Pi 首次归档失败已保留，后续图片/浏览器观察完成但严格 parent/session 归档问题曾独立阻断。该证据支持“视觉输入路径曾被真实消费”，不等于本次 quota 阻断后的新资格。
- 既有成功记录的 cost 字段可得但只是客户端/provider 计算值，不是 Meter 账单；例如 `20260920-141339-6138c072` 的 native usage cost 汇总为约 `0.0474915168`（币种和结算未知）。本次三次 429 没有 usage/cost，不能估价。
- `runs/integration/20260921-235700-pi-braid-ca880d/effective-config.json` 仅声明过 GLM UI profile，Braid 在预期观察前退出，没有 GLM assistant response；不能把声明当成 GLM tool-call/reasoning 证据。

## 严格实施顺序

1. 先冻结 `harness/models.json` 的实际模型 descriptors 和 role/protocol spike 结果；没有成功请求时保留接口 unknown，禁止进入四 variant 正式 score。
2. 新增两个 profile 与五个 native role 的材料及静态 owner 字段；把 `context` 从 `native_profiles.py` 硬编码移到 profile/role effective contract，保持现有 Pi/Codex 模板消费者单一读取点。
3. 让 `scripts/profiles.py` 读取 `variants/<variant>/variant.json`，校验 login 唯一、defaults 只指向已选 profile、SVC path/hash 与 model input/reasoning/role consumer 一致；删除对 `preset.json` 的读取。旧 `pi-generalist`/`codex-generalist` 只保留历史归档兼容，不能继续出现在活动矩阵。
4. 更新 `scripts/native_profiles.py` 展开公开描述、role skills/MCP/context 和冻结 SVC 材料；输出 internal binding 与 runtime-safe assignee projection 分离，运行时只收到 login/description/能力说明。
5. 更新 `scripts/factory.py` 与 `scripts/package_agent.py` 让 effective variant/material manifest 进入同一 ZIP；同一 bytes 供 hosted/local runner，保留 source revision、path hashes、effective digest。先跑无模型 fixture，不上传 Competition。
6. 更新 `scripts/batch.py`/实验 controller 只消费显式 `{variant, package_sha256, venue, task, model_config_id}`；旧 preset 目录和历史 run 只读，不回写。
7. 最后同步 `tests/test_profiles.py` 及相关静态/manifest checks，跑四 variant effective diff；接口 spike、Pi 分层和 package qualification 全过后再由主 Agent申请 implementation impact handshake。

## 最小可运行检查

实施后最小检查应保持一条命令一类判据：

- `PYTHONPATH=scripts python3 -m unittest tests.test_profiles`：未知 profile/role/skill/path、重复 login、defaults 越界、仅实际消费者 digest 变化。
- 一个无模型 Python fixture 调 `profiles.resolve` 四 variant，断言各 effective manifest 只出现上表差异；`pi-team-mixed` 与 `pi-team-vv` 的 profile/role/model/skill/MCP/context digest 相同，只有 SVC preload/hash 不同。
- `native_profiles.materialize` 在临时目录展开两个 profile，断言每个 parent/role 的实际 model、reasoning、context、skills、MCP、tool list 与 source 一致，且 generated runtime instruction 不含 `profile`、`preset`、variant ID 或模型路由字段。
- 用冻结 SVC source 在临时目录执行 `svc lookup --path index.md`、两个 preload path，并比对 source revision/path hashes；禁止从 Factory 自己维护第二份 canonical 正文。
- 用脱敏 HTTP fixture 返回成功 tool-call、reasoning、image 及 429/400，断言 adapter 保留实际 wire fields、错误归属和 `usage/cost=null`；fixture 不能替代 quota 恢复后的真实最小调用。
- package prepare-only + local official runner fixture：检查 ZIP hash、manifest、标准 `frontend/package.json`/`backend/package.json` 入口；不以 local-only `deploy.sh` 通过资格。

## 失败归属与残余

当前 spike 的唯一真实失败是比赛 key 的 free quota exhausted / balance too low（HTTP 429），归属外部 Meter/网关；不应修 `profiles.py`、Pi adapter 或以 Kimi/Max/Playground 替换目标模型。`deepseek-v4-flash`、`glm-5.3-flash` 的成功文本 tool-call 和 reasoning wire shape 仍 unknown；视觉裸 HTTP image response 也仍 unknown，既有 Pi 视觉归一化证据只能复用为部分支持。

实施前仍需由主 Agent决定并在 handshake 中记录：公开 login 大小写与 description 字节上限；variant 文件是否命名 `variant.json`；profile context 与 role context 的合并规则；SVC preload 是否注入 instructions 还是由 runtime 按路径 lookup；specialist 是否真的进入首轮能力集；以及 quota 恢复后每模型一次成功 tool-call、一次 reasoning 形态和视觉 data URL 的重验。没有这些证据，四组只能完成静态装配，不能声称模型能力资格或正式可比实验。
