# Provider fallback 调查与当前建议（2026-10-02）

## 当前账户事实

本轮按实际激活 alias 决定供应商集合，不按品牌数量扩张。当前重点是 ARK、千问普通/Token Plan、百度千帆；DeepSeek 原厂 Flash/V4.1 排除，BigModel/Kimi 只在主表明确条件下复核。目录存在不能推导模型可用性。

用户从 Helium 后台读回的事实：

- 阿里百炼/千问 Token Plan 是 Essential，2026-10-02 23:04:20 月已用 57.86%；可见 `glm-5.3`、`deepseek-v4-flash-0731`、`deepseek-v4-pro`、`deepseek-v4-pro-0813`，不列 Flash/K3。页面 endpoint 为 `token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`，私有 env 历史 endpoint 是用户指定的 `token-plan.maas.qianwenaiapi.com`，两者差异须在真实请求前核对。它与下文百度千帆个人 Token Plan 是不同账户/服务，不能混写权益。
- ARK Pro 页面显示 5 小时、周、月额度均 0% 已用，当前实际配置模型 ID 为 `glm-5.3-flash`、`glm-5.3`、`kimi-k3`、`kimi-k2.7-code`、`deepseek-v4-flash`、`deepseek-v4-pro`。页面可见不等于工具、流式或 Responses 已验收。
- 普通 API 免费额度页：`kimi-k3` 剩 798.3K/1M，`deepseek-v4-flash-0731` 剩 1M/1M，均未开启“用完即停”；裸 `glm-5.3` 免费额度/期限显示 `-`（未知，不能当零），`ZHIPU/GLM-5.3-Flash` 显示 0/0（未获免费配额，不能解读为普通 API 余额耗尽）。普通账单本月 74.67 元，总含订阅 153.67 元；余额未知，普通 API 不是零成本。
- 旧阿里 Coding Plan 与当前 Token Plan Essential 是不同服务；旧 Coding Plan 条款不套用 Token Plan，也不靠用户确认豁免。当前方案不把旧 Coding Plan 纳入候选。

## 当前采用的候选链

稳定客户端 alias 继续使用精确模型名；`chat`、`responses`、视觉等是能力字段，不新增 `chat-code`/`responses-code` 等模型别名，以免破坏现有预算护栏。

| 精确 alias | 候选顺序 | 采用理由与缺口 |
| --- | --- | --- |
| `glm-5.3-flash` | **默认** 千帆 Token Plan `glm-5.3-flash` → ARK `glm-5.3-flash`；若千帆 Plan 能力未成立，则 ARK → 普通 Qwen `ZHIPU/GLM-5.3-Flash` | 三条 deployment 均已完成最小文本 Chat 200；千帆 Plan 已购且后台明确列 Flash，优先使用。只保留两 route，不混合文字/视觉供应商；工具/视觉仍需 e2e 验收。 |
| `glm-5.3` | inactive（GLM root 本轮未选） | 后续若启用：千帆个人 Token Plan 权益和部署明确可用时，建议千帆 Token Plan → ARK；Plan 未确认则 ARK → 千帆普通。普通千帆活动价不能替代能力/权限验收。 |
| `kimi-k3` | ARK `kimi-k3` → 普通 Qwen `kimi-k3` | 两条精确 ID 均已完成最小文本 Chat 200；Token Plan/千帆无同版本证据，普通 Qwen 费用和“用完即停”边界仍需记录。 |
| `kimi-k2.7-code` | ARK `kimi-k2.7-code` | 当前没有已确认的等价备用；用户只排除 highspeed 变体，不能扩大为其它未确认模型。无 candidate 才停止该 alias。 |
| `deepseek-v4-flash-0731` | 千帆 Token Plan → 千问 Token Plan → 普通 Qwen | 三条精确 ID 均已完成最小文本 Chat 200；同供应商 Token Plan→普通 API 只覆盖额度/限流，不宣称容量故障隔离。ARK `deepseek-v4-flash`、DeepSeek 原厂别名继续排除。 |
| `deepseek-v4-pro` | Token Plan `deepseek-v4-pro` → ARK `deepseek-v4-pro` | 两个账户页面均可见；需验收实际 wire ID、工具/Responses 兼容和额度。 |

视觉请求只能使用已做视觉真实验收的同模型 deployment；不能用文字模型 fallback 代替。Flash 的视觉链仍需单独验收，文本 HTTP 200 不证明视觉能力。

候选链是实验方案提议，不代表已受理或已启动。每个候选应在冻结配置中保留 provider、plan、wire model、endpoint 非敏感部分和账户身份。

## LiteLLM 1.102.0 实际能力

已定位本机 uv 缓存：`/Users/lanzhijiang/.cache/uv/archive-v0/zil2Bd8JCYkrBEUd/litellm-1.102.0.dist-info/METADATA`，版本为 1.102.0；只读源码，未安装或修改依赖。

冻结 `litellm/router.py` 确认原生 Router 有：

- `fallbacks`、`max_fallbacks`、`num_retries`、`RetryPolicy`、`allowed_fails`、`cooldown_time`；同 model group 多 deployment 也可失败重选。
- `enable_weighted_failover=True` 只在 async 路径启用，并受 `max_fallbacks` 限制。
- Chat 流在尚无生成内容时可 fallback；已生成内容后抛原始异常。Responses 流在已有内容时会构造 continuation input 再 fallback，属于语义重写，不能当无损重放。
- Proxy 会读取顶层 `router_settings` 并传给 Router，但当前 `scripts/hackathon_gateway.py` 只调用 `bin/litellm --config`，现有 `harness/model-gateway.json` 没有 router settings。

当前 launcher 的根边界仍是问题：`prepare_catalog()` 每个 alias 只保留一个 deployment；所以原生 fallback 能力尚未被实例配置使用。最小接入应让冻结配置同时包含链上候选、把 API 形态作为请求能力字段，并在现有 callback 中记录每个尝试的 `alias / deployment_id / provider / plan / wire_model / config_sha256 / run_id / attempt_id / incarnation / attempt_index / status`。不应另造代理。

## 失败处理建议

- 对 429、连接失败、503：按冻结策略做一次短退避，再尝试同链下一个候选；不在同一通道重复打爆额度。403/402/401/400、模型不存在、权限或工具 schema 不兼容：终止当前 deployment，并可继续到已冻结且获许可的下一个候选；只有没有 candidate 才停止整个 alias/实验。
- 套餐耗尽类 429 进入 cooldown，不把 retry 当作额度恢复。每次失败保留具体 HTTP 状态、错误类型和响应诊断，不能只写“rate limited”。
- 流式首 token 前失败可以切换；已发出内容后，Chat 按冻结 1.102.0 行为终止，Responses 的 continuation fallback 只有在单独验收通过后才能启用。
- 记录 LiteLLM 实际选择的 deployment；仅记录客户端 alias、或仅看到 HTTP 200，都不足以证明 route identity。

## 未验边界

- 当前 Proxy 启动参数与 `router_settings`、fallback 链和自定义 callback 的组合尚未实际启动验证。
- 各账户精确 wire ID、工具调用、流式、视觉、Responses 语义和剩余额度尚未逐项真实验收。
- Token Plan 页面 endpoint 与私有 env 历史 endpoint 的差异尚未通过安全的目录/最小请求核对；不读取或输出凭据。
- ARK `deepseek-v4-flash` 与 Token Plan/普通 Qwen `deepseek-v4-flash-0731` 没有版本等价证据，因此不纳入链。

官方依据：[百炼 Token Plan 个人版](https://help.aliyun.com/zh/model-studio/token-plan-personal-overview)、[Token Plan 快速开始](https://help.aliyun.com/zh/model-studio/token-plan-team-quickstart)、[百炼限流](https://help.aliyun.com/zh/model-studio/rate-limit)、[方舟 Coding Plan Codex 配置](https://docs.volcengine.com/docs/ark/coding-plan-personal-ai-codex?lang=en)、[DeepSeek 限流](https://api-docs.deepseek.com/quick_start/rate_limit/)、[DeepSeek 错误码](https://api-docs.deepseek.com/quick_start/error_codes/)、[DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls/)、[LiteLLM Router fallback/retry 源码对应文档](https://docs.litellm.ai/docs/completion/reliable_completions)。

本调查未读取或输出凭据值；Helium 仅用于只读后台核验，未修改账户、未安装依赖、未部署或恢复实验，未运行 Factory/Braid 测试。已授权的有界直连短 Chat 证据见下文“Helium 后台核验与当前冻结补充”及 WorkSSD probe 原件；未启动官方 run 或本地冻结网关。

## Factory 产物路径审计（WorkSSD 约束）

用户规定 Factory 项目产物只能落在 WorkSSD。当前生产者的边界如下；本节只记录观察，不执行清理或迁移。

| 生产者 | 当前默认/显式路径 | 能否现有选项绑定 WorkSSD | 缺口 |
| --- | --- | --- | --- |
| `scripts/runtime.py prepare/path` | `cache_path()` 硬编码 `Path.home()/'.cache/factory26'`，会写用户 home；`prepare` 没有 cache 参数。 | 不能。`linux --output` 可把导出的 runtime 放到 WorkSSD，但 npm/Playwright 准备缓存仍在 home。 | 需要源码增加显式 cache root，并拒绝解析到 WorkSSD 外；否则 `runtime prepare` 仍越界。 |
| `scripts/runtime.py linux` | `TemporaryDirectory(prefix=...)` 默认使用系统 temp，当前 macOS 通常是 `/var/folders/...`，不是 `/tmp` 文字路径；最终 `--output` 可显式放 WorkSSD。 | 不能满足绝对约束：output 可绑定，但临时 Docker build context 受 `TMPDIR`/系统 temp 控制，没有项目级 WorkSSD 参数或校验。 | 必须由后续源码把 build context 临时根绑定 WorkSSD；不能把系统 temp 当例外，也不能假设 `TMPDIR` 已覆盖所有路径。 |
| `scripts/runtime.py host-exp` / `ensure_host_runtime` | `--output`、`--cache-root`（由调用方传入）均可显式路径；实验环境 selection 保存 `cache_root`。 | 可以，前提是 recipe/environment selection 使用绝对 WorkSSD `cache_root`；`lab.exp.readiness` 会消费冻结值。 | 没有全局 WorkSSD 强制；任意旧 recipe 仍可声明 home 或其它盘。需要入口级根校验才能保证。 |
| `scripts/package_agent.py` | `--cache-root` 可指定；默认 `ROOT/runs/material-cache`，在 WorkSSD 仓库内。stage/output 由 `--stage`/`--output` 指定。 | 可以，现有选项足够；应总是显式传 WorkSSD cache/output。 | 无强制根校验，传入 `~/.local/share` 仍会被接受；默认只保证当前仓库工作树。 |
| `lab.exp` artifact store / executor | store 默认实验目录下 `artifacts`；environment selection 的 `cache_root/artifacts` 会作为共享 store，路径由 recipe 冻结。 | 可以，recipe 的 execution storage 和 `cache_root` 设为 WorkSSD 绝对路径。 | `Path.expanduser/resolve` 接受 home；没有“必须 WorkSSD”策略检查。 |
| `lab/control.py` | controller Unix socket 明确创建在 `/tmp/lab-<token>/control.sock`，finish 时删除目录。 | 不能靠现有 CLI 选项绑定；它也是 Factory 实际产生的运行状态。 | 必须由后续源码支持 run-scoped WorkSSD temp root，并把 root 写入 experiment/attempt；硬编码 `/tmp` 在绝对约束下是阻塞缺口。 |
| `lab/arc_bench/arc_bench_adapter.py`、`model_facts.py`、`package_arc_replay.py`、`playground.py` | 多处 `tempfile.TemporaryDirectory` 未指定 dir，默认系统 temp；`playground.py` 还使用 `Path.home()/'.config/factory26'` 保存配置/`llm.env`。 | 不能满足绝对约束；`TMPDIR` 只能影响部分 tempfile，不能覆盖硬编码路径，也不能作为完成证明。 | 必须由后续源码把运行临时根、配置根改为显式 WorkSSD experiment/deployment 路径，并拒绝 home/系统 temp。 |
| `lab/docker_endpoint.py` / Docker CLI | 当使用 `DOCKER_HOST` + TLS 且未给 `DOCKER_CERT_PATH` 时回退 `Path.home()/'.docker'`；Docker context 自身也由 Docker CLI 管理，代码只读并冻结 endpoint。 | 可以通过显式 `DOCKER_CONFIG`/`DOCKER_CERT_PATH` 或 context 配置间接绑定；当前代码没有项目级参数。 | 需要在 endpoint freeze 时记录并校验 Docker 配置/证书根；否则宿主 home 仍可能成为外部缓存或凭据来源。 |
| `braid-console/service.py` | `prepare` 的 destination 必须由调用者传入，代码只 `expanduser().absolute()`；manifest/app 写入该目录。 | 可以，CLI 传 WorkSSD destination；当前长期 service 规则会拒绝 `runs` 等临时目录。 | 没有 WorkSSD 根校验，传 home 仍可成功；需要后续入口策略而非重复清理。 |

因此当前最危险的隐式越界是 `scripts/runtime.py cache_path()` 的 `~/.cache/factory26`、`lab/arc_bench/playground.py` 的 `~/.config/factory26`、`lab/control.py` 的硬编码 `/tmp` socket，以及 ARC 适配器未指定目录的系统 temp。已有 `--output`、`--cache-root`、recipe `cache_root`、artifact `store` 能覆盖大多数持久 runtime/material/artifact 路径，但没有统一的 WorkSSD 根策略，不能声称已满足绝对约束。系统 temp、socket 和中间目录同样属于 Factory 实际产生的路径，不能排除。后续源码必须集中解析显式 WorkSSD root，对所有输出、cache、store、配置、socket、temp 和日志做 `resolve().is_relative_to(root)` 校验，并核对真实 mount 与符号链接解析结果；WorkSSD 不足或路径越界必须在 prepare/launch 前阻塞，不得靠 `TMPDIR` 或用户约定放行。

## 官网完整生成与 fallback 接入（实施准备，只读）

首轮目标仍是由 I14 Harness 冻结并消费同模型候选链，避免把 429 留给热修复。Hosted 现有接口只冻结单模型 metadata：`arc_matrix.py` 要求 `model_config` 含 `model`、`visual_model`、`base_url`、`provider`，`hosted.py::_context` 验 HTTPS endpoint；`controller.py::_load_deployment` 只接受私有 `credential_file`/`cookie_file`。Hosted dispatch 的 `/submissions` payload 只上传 agent ZIP、`credential_mode` 和一个用于 CreateRun 的 `api_key` secret；`runner._environment` 的全量环境注入只适用于本地执行器，Hosted 不会自动把 credential file 的所有变量发送给平台。因此现有 `credential_file` 不能写成“已注入多秘密”。

### 最窄 artifact 接缝

`start_shared_proxy(runtime, run, env)` 只是 Portless HTTP 共享代理（检查 `X-Portless`），不能复用为 LiteLLM Router。I13/I14 Pi runtime 默认不含 LiteLLM：`submission/Dockerfile`/`build.py` 只有 `BACKEND=codex` 分支安装并生成 `litellm[proxy]==1.102.0` 与 `runtime/bin/litellm`。首轮拟沿现有 Linux/Python 3.12 x86_64 生产接缝附带冻结 LiteLLM 1.102.0，记录依赖树、`runtime/bin/litellm` 与 lockfile 身份，不在官网运行时安装。

在 I14 `generate()` 建立 run/work 和 bindings 后、Braid 前，增加与 shared proxy 对称的 run-owned `start_model_gateway(runtime, run, env, catalog)`：从冻结 catalog 生成 sandbox-local state，启动 `runtime/bin/litellm --config ...`，等待 liveliness，返回 loopback `/v1` 和 owner handle，finally 同一生命周期清理。Pi native route 指向 loopback；Hosted `model_config.base_url` 仍填平台要求的 HTTPS ARK root，不把 loopback 写入 Hosted 字段。sandbox state/socket/request metadata 是官方平台现场；本地可控 catalog、recipe、ZIP、cache、归档、日志仍物理在 WorkSSD。

Router使用原生`model_list/router_settings`；`hackathon_gateway.py::prepare_catalog()`的“每alias单deployment”是待改单点，改为冻结同alias candidate list，并由既有callback记录deployment、attempt、status、stream边界和config SHA。不造公网代理或新Hosted schema。

供应商顺序不能靠JSON列表顺序或随机权重表达。只读1.102.0源码`utils.get_order_filtered_deployments()`与`Router._async_function_with_fallbacks_common_utils()`已确认：同alias deployment可用`litellm_params.order`，默认选择最低健康order，失败后原生async fallback按较高order接续。首版两通道分别order=0/1，保持相同客户端模型名；无需生成`chat-code`或provider后缀alias，也不用weighted failover。拟用`num_retries=0`、`max_fallbacks=1`，每次Router调用先主通道一次、失败再备用一次；具体timeout/cooldown及原生客户端重试一并冻结，避免叠成无界重试。该代码能力尚未在本项目gateway的实际Chat流操作中验收。

### 多 provider secret 的真实交付边界

`package_agent.py::write_tool_credentials()`/`write_zip()` 有可复用的 `.private/*` 合同：私有文件只能来自 Git 忽略位置，ZIP 条目为 0600，manifest 记录 hash；但当前它只服务 `CONTEXT7_API_KEY`、`EXA_API_KEY`，`run.py::tool_environment()` 也只消费这两个变量。不能据此声称模型 secrets 不会进 ZIP，也不能把工具私有配置当作 provider 注入能力。

当前采用的最窄方案是扩展同一 private artifact contract，增加独立 provider credentials file：仅含实际选定 ARK、Token Plan、普通 Qwen 的 credential environment names/values，权限 0600；公开 catalog 只保留 `os.environ/<NAME>` 引用及 provider/plan/wire model/deployment ID，公开 manifest 只记录该私有文件内容 hash，不记录 secret 值。选择私有agent payload内的`.private/provider-env.json`，由Harness入口读取后只交给gateway进程；此路径复用ZIP上传，不要求平台新增多secret mount。Python ZIP解包不自动恢复文件权限，入口须实际设private目录0700/文件0600，再读取并限制变量作用域；它仍须通过解包、权限恢复与回收验收，不能以已有工具私有文件证明模型接线已运行。若用户不认可这种秘密交付范围，则包内多provider fallback不能启动；另有平台secret mount时可采用其真实接口，当前未发现该能力。不用ambient env、自制加密或公网隧道补缺口。

raw error/stream 日志须按这次实际注入的 secret values 精确 redaction，普通证据归档不复制`.private`原件；确需保留的原始私有ZIP继续0600存放，不能将含秘密原件发布为普通evidence或版本库内容。保留credentials file hash、变量名集合、注入方式和deployment identity。这个provider credentials file是新增能力、待具体实施复核的秘密交付范围，不是现有`credential_file`已具备的事实。Pi与e2e只取得本地gateway访问token，上游供应商keys不向成员进程广泛继承。

### 启动、路由及验收

WorkSSD 冻结 runtime、ZIP、recipe、credential contract、bindings、catalog；Hosted self-funded 创建 snapshot/run；sandbox 解包私有 provider credentials，启动本地 gateway 并健康检查；Pi/Braid 消费稳定 alias；Router 在首 token/工具副作用前按冻结链 fallback；结束后归档 platform identity、workspace ZIP、gateway metadata、native homes、Braid DB/WAL 与 `process-evidence/*`。每次 route 至少记录 alias、成员 profile/Braid session、attempt index、deployment ID、provider、plan、wire model、config SHA、HTTP status/诊断、cooldown、首 token和终止状态。

Chat 首 chunk 前错误可 fallback，首 chunk 后保留部分输出并抛原始错误；Responses continuation 不默认启用，工具副作用开始后不得自动重放。首轮验收需有：公开manifest/日志无明文泄露，私有ZIP按private contract读取；真实首token前429/连接失败保存原错并切换下一deployment；同一Braid session无重复工具副作用；workspace bundle绑定Hosted identity、ZIP hash、native/Braid与cgroup事实。实际路由操作只能说明被观察到的错误类型；没有429原件时不能宣称429路径实测通过，不模拟供应商或编写设施测试。未实测项是开工后验收条件，不是取消首轮fallback的理由；私有payload未获准/无法消费或gateway不可达才是具体阻塞，不因平台没有新增secret mount就否认ZIP承载方案。

`lab.exp` Hosted export 目前只保存平台 JSON/日志/traceability；旧 `hosted_monitor.py` 才能 GET workspace bundle 并读取 native homes、Braid DB/WAL、process evidence。生成 OOM 必须读取 workspace 内 cgroup counters/process evidence，application replay 不能替代生成事实。

## 价格、权益与当前 catalog 收敛（2026-10-03，只读）

价格只能影响候选顺序和预算记录，不能把低单价当作有效成本：套餐 Credits、活动价、账户余额、模型权限、工具/流式能力和失败后的机会成本仍须分别记录。官方公开资料给出的可比事实如下：

| 通道/模型 | 官方公开计价或权益 | 对今晚决策的含义 |
| --- | --- | --- |
| 百度千帆普通 GLM-5.3 | 2026-09-24—10-07 活动价：输入 4.8、输出 16.8、缓存命中 1.2 元/M；原价 8/28/2；`glm-5.3`。活动页按千 tokens 展示，换算到 M 才得到该表数字。 | 价格显著低于 BigModel GLM-5.3 的 8/28/2，但千帆普通 API 尚无真实调用、工具/流式验收，不能自动成为主链。 |
| 百度千帆个人 Token Plan GLM-5.3 | 专用 endpoint `https://qianfan.baidubce.com/v2/tokenplan/personal`、专用 key；公开资料确认同名请求 ID `glm-5.3`，但用户购买档位、Credits 抵扣和剩余权益未记录。 | 可作为 GLM 的隔离候选；同名只证明请求 ID 相同，不证明推理版本、工具协议或套餐抵扣等价。 |
| BigModel GLM-5.3/Flash | 分别 8/28/2 与 0.8/2.8/0.23 元/M；Flash 有历史短文本 200，但账户当前可用性仍需核实。 | 低价 Flash 不能替代 e2e 优先级；普通按量价格也不能证明今晚余额或权限。 |
| Kimi K3 | 输入 20、输出 100、缓存读 2 元/M；缓存写 5min 20、1h 40 元/M。 | 价格高，保留 K3 链是因为 ARK/普通 Qwen 账户事实和模型需求，不把低价假设套用到 K3。 |
| 千问 Token Plan Essential | 官方 FAQ 列 Essential 25,500 Credits/月；公开概览页面档位展示存在更新不一致，用户后台事实仍是 Essential、已用 57.86%。专用 Base URL/key 与普通 API 分离。 | Credits 不是元/M；不能把 79 元或 Credits 直接换算成一次实验成本，需记录消耗和剩余机会成本。 |

官方依据：[千帆国庆活动及 GLM-5.3 价格](https://cloud.baidu.com/product/qianfan_home/campaign.html)、[千帆模型列表](https://cloud.baidu.com/doc/qianfan/s/rmh4stp0j)、[千帆个人 Token Plan 接入](https://cloud.baidu.com/doc/qianfan/s/kmracfgi2)、[千问 Token Plan 概述](https://platform.qianwenai.com/docs/token-plan/overview)、[千问 Token Plan FAQ](https://platform.qianwenai.com/docs/token-plan/personal/token-plan-personal-faq)、[Kimi 定价](https://platform.kimi.com/docs/pricing/chat)、[BigModel 定价](https://docs.bigmodel.cn/cn/guide/start/pricing.md)。

### 配置状态与可采用链

`harness/model-gateway.json` 当前实际已有 deployment 行的范围已覆盖本轮选定的 Flash、K3、DS0731 路由：已列 BigModel `glm-5.3-flash`/`glm-5.3`、Kimi `k3`/`k2.7-code`、普通 Qwen Flash/GLM/K3、Token Plan/普通 Qwen `deepseek-v4-flash-0731`、ARK Flash/K3、以及千帆 GLM-5.3 普通/Token Plan、千帆 Token Plan Flash/DS0731 行。ARK 的 `glm-5.3`、`kimi-k3`、`kimi-k2.7-code`、`deepseek-v4-*` 尚未进入该 catalog；它们是账户配置事实或候选，不是当前网关可调用 deployment。当前目录也没有把每一条拟议链完整物化为 `factory26_default`；`prepare_catalog()` 仍只会选择一个 deployment，不能把目录存在写成 fallback 已启用。

因此首轮只按主表冻结实际激活 alias；本段只记录状态和缺口，不另维护推荐链：

- Flash：catalog 有千帆 Plan、ARK、普通 Qwen 三条；本次三条最小文本 Chat 均 200，视觉与工具仍需整体验收；BigModel Flash 不激活。
- K3：ARK 与普通 Qwen K3 row 均已进入 catalog，最小文本 Chat 均 200；千帆无同版本证据。
- `deepseek-v4-flash-0731`：千帆 Token Plan、千问 Token Plan、普通 Qwen row 均已进入 catalog，最小文本 Chat 均 200；两条千问通道不能宣称隔离容量型 429。
- GLM-5.3：本轮 inactive；其千帆 Plan/普通、ARK 等候选不装配首轮 key。

“已配置”仅表示集中 catalog 有精确 deployment row；“拟补 deployment”表示账户有模型但 catalog 没有该 row；“公开候选”只表示官方资料显示同名/价格，不能进入 Router。实际首轮调用前必须把选定链的每个 deployment、精确 wire ID、endpoint 类型、plan、credential env 引用和能力验收状态冻结；不因未知价格声称某普通 API 最省，也不因活动价扩大首轮 alias。

### 首轮实际消费边界（避免目录默认吞入非本轮路由）

本轮不能让 `prepare_catalog()` 遍历全目录后按每 alias 默认值隐式激活 BigModel GLM、Moonshot K2.7 或其它未选 deployment。首轮应在同一冻结 catalog/config 中显式给出实际激活 alias 集合及各自 candidate chain，只装配这些 deployment 的 env 引用和 `.private/provider-env.json` 变量；目录中其它行只保留为未激活候选，不消耗首轮凭据或预算。

首轮 profile 消费面是 Flash root/fast、e2e、visual，以及内部 DeepSeek；advisor 使用 K3；GLM root profile 未选。内部 native 原文仍是 `deepseek-v4-flash`，gateway 稳定 alias 是 `deepseek-v4-flash-0731`，必须用既有 `FACTORY26_MODEL_BINDINGS` 的精确 selector→`model_id` 映射（`native_model_route()` 已支持），不能让默认 `factory26` route 吞掉 0731 版本差异。视觉只绑定已真实验收的视觉 deployment。

| 首轮意图 | 现有 catalog 状态 | 需补/冻结的边界 |
| --- | --- | --- |
| Flash 文本/视觉 | catalog 有 ARK Flash、普通 Qwen Flash；视觉 deployment 与文本能力仍需单独确认 | 只激活真实视觉验收通过的同模型链；不要因 catalog 有 BigModel/Command/Gongji Flash 自动扩链 |
| K3 advisor | catalog 有普通 Qwen K3，ARK K3 仅账户配置，未入 catalog | 补 ARK K3 deployment row 后才能形成 ARK→Qwen 链；未补前不能声称该链已可用 |
| 内部 DeepSeek | 当前 native `deepseek-v4-flash` 与 gateway `deepseek-v4-flash-0731` 名称不同；catalog 仅有 Token Plan 0731 | 冻结 selector→`model_id=deepseek-v4-flash-0731` 的明确映射；普通 Qwen 0731 是否加入由实际 catalog row/账户权限决定，不能靠 alias 推断 |
| GLM root | profile 未选；catalog 有多家 GLM 行，千帆两条同 ID | 不激活、不装配其 secrets；千帆低价只作为后续隔离候选，不改变 e2e 优先级 |

因此“已配置”还要分为“catalog 有 row”和“首轮激活”；只有后者能进入 Router。缺 deployment 的 ARK GLM/K3/K2.7/DeepSeek 行属于拟补项，不能在首轮配置里以默认值出现；不另造全局路由表，激活集合与链随当前实验 recipe/catalog 一起冻结。

## 实施接缝落地记录（2026-10-03）

已在负责范围落地可供 I14 入口消费的 helper（未启动）：`scripts/agent_support.py::read_provider_environment(path, allowed=None)` 只读 0600 JSON、拒绝未知/空变量；`start_model_gateway(runtime, run, env, config, bindings=..., gateway_routes=..., port=4011, host='127.0.0.1', provider_env=None, preserve_parameters=...)` 要求冻结 `runtime/bin/litellm`、run-local config 和 loopback，物化 `general_settings.custom_auth`、现有 callback、`use_chat_completions_api`，展开 `api_base` 环境引用，复制兼容层并把 `runtime/python` 加入 gateway `PYTHONPATH`，创建 run-owned `model-gateway/`、request log/bindings/`gateway-routes.json`，等待 `/health/liveliness` 后返回 `{process, identity, endpoint, config, routes, log, pi_environment}` handle；`stop_model_gateway(handle, run)` 只清理该 owner。provider-env 值只进入子 gateway 环境，Pi/e2e 不继承上游 keys。公开 package 应将实际 active chain 作为 `gateway-routes.json` 输入并记录其 hash；原始合同是 `{stable_alias: [ordered_deployment_id, ...]}`，不含 endpoint 或 secret。Native bindings 仍由入口按同一冻结选择生成，Hosted 不依赖 `FACTORY26_GATEWAY_ROUTES` ambient env。

`scripts/hackathon_gateway.py` 现支持 0600 `.env` 或 `.json` provider-env（可为 `{environment: {...}}`），支持 `--alias ALIAS` 限制激活集合，`--route ALIAS=DEPLOYMENT_ID[,DEPLOYMENT_ID...]` 选择有序同 alias deployments；`prepare_catalog()` 为每个候选写入 LiteLLM `litellm_params.order`，routing snapshot 同时记录 order、deployment、provider、plan、wire model 和 endpoint env 引用。`hackathon_gateway_compat.py` 的 request/failure/stream 记录会按实际 gateway 环境中的 key/token/master key 做落盘前精确 redaction；错误原件只保留脱敏后的诊断，不模拟 429。

Linux package 接缝需复制到 artifact 的最小源码集合为 `scripts/hackathon_gateway.py`、`scripts/hackathon_gateway_compat.py`、`scripts/responses_compat.py` 和集中 `harness/model-gateway.json`；运行时必须提供 Linux x86_64 CPython 3.12、`runtime/bin/litellm`、`runtime/python/litellm` 及其冻结 lock/依赖。`.private/provider-env.json` 仅装配实际激活 alias 所引用的 env names，ZIP 私有条目 0600，入口解包后恢复 `.private` 目录 0700/文件 0600，再只把它交给 gateway；公开 manifest 仅保存私有文件 hash和 catalog/config SHA，不复制原件到普通 evidence。上述 package/build 复制和 artifact 入口由材料生产负责人接续；本次未启动官方 run、未运行 Factory/Braid 测试。

在冻结 runtime 交付前，已用现有私密环境做了有界的直连短 Chat 验证；只把状态、响应模型和 usage 写入 WorkSSD 原件（不保存 key 或原始响应）：`runs/iteration14/overnight-20261003/provider-requests/chat-probes.json` 与 `secondary-probes.json`。千帆 Token Plan、ARK、普通 Qwen 的 Flash 精确请求均 HTTP 200；响应模型分别为 `glm-5.3`、`glm-5-3-flash`、`ZHIPU/GLM-5.3-Flash`，三者 usage 均为 prompt 17 / completion 8 / total 25。千帆 Token Plan、千问 Token Plan、普通千问的 `deepseek-v4-flash-0731` 均 HTTP 200（88/8/96）；ARK 与普通千问 `kimi-k3` 均 HTTP 200（分别 90/8/98、90/11/101）。这证明精确 wire ID、账户可达和最小文本请求，不证明工具/视觉/stream 或 429 fallback；没有模拟 429，也没有启动官方 run。

## Helium 后台核验与当前冻结补充（2026-10-03）

通过用户已登录 Helium 标签页只读核验（未复制或输出密钥值）：

- 百度千帆 Token Plan 个人版当前为“国庆限定·尊享版”，剩余 5 天，到期 `2026-10-07 23:59:59`，余量 `88,000 / 88,000` 积分；OpenAI 兼容 Base URL 为 `https://qianfan.baidubce.com/v2/tokenplan/personal`。模型切换列表明确包含 `GLM-5.3-Flash`、`GLM-5.3`、`DeepSeek-V4-Flash-0731`、`DeepSeek-V4-Pro` 等；因此 Flash Plan 是已购且优先可选的精确能力候选，不能再按旧文档“Token Plan 不列 Flash”排除。页面还显示 Coding 配置名 `qianfan-code-latest`，但本轮稳定 alias 仍使用精确 provider model ID，不直接把配置别名当 wire model。
- 方舟 Coding Plan 当前为 Pro 包月，2026-10-02 21:05 至 2026-11-02 23:59，近 5 小时、周、月用量均 0%；权益列表包含 `GLM-5.3-Flash`、`GLM-5.3`、`Kimi-K3`、`Kimi-K2.7-Code`、`DeepSeek-V4-Flash`、`DeepSeek-V4-Pro`。模型可见和额度可用仍不等于工具/流式真实验收。
- 智谱后台价格页显示 GLM-5.3 按量 8/28/2 元/M，GLM-5.3-Flash 0.8/2.8/0.23 元/M；本次读取的是公开价格页，不把它当余额证明。此前账户零余额事实仍由用户后台核验记录负责，本轮不再把 BigModel 加入首轮链。

因此当前主表的 Flash 默认链应更新为：千帆 Token Plan `glm-5.3-flash` → ARK `glm-5.3-flash`；若千帆 Plan 在本轮实际工具/视觉能力不成立，才启用 ARK → 普通 Qwen `ZHIPU/GLM-5.3-Flash` 作为两路替代。两路均使用同一个稳定 alias 和同一 gateway 能力配置，不拆文字/视觉供应商。GLM-5.3 root 仍 inactive；K3、DS0731 依照主表的 catalog/拟补边界，不因后台模型可见直接激活。

当前 WorkSSD 没有发现可直接消费的冻结 `runtime/bin/litellm` 或 `runtime/python/litellm`；已实现的 gateway helper 因此尚未做本地网关启动验收，直连短请求证据不能替代它。材料生产必须先交付 Linux/Python 3.12 x86_64 LiteLLM 1.102.0 runtime 及 package support 文件，随后由 I14 入口做真实短 Chat/工具/视觉验收；不以 pycompile 或假 429 代替。

### Mac host gateway 实际接线（2026-10-03）

为验证接缝，复用了 WorkSSD `.adapter` 中只读的 LiteLLM 1.102.0，建立了独立 host runtime（明确是 macOS/CPython 3.13 证据，不外推 Linux artifact）。冻结 routes 原件为 `runs/iteration14/overnight-20261003/host-gateway-014504/gateway-routes.json`，形状为 alias 到有序 deployment ID 列表；过滤后的 `.private/provider-env.json` 为 0600，仅含八个选中 endpoint/key 环境变量，未写入正文。helper 成功启动 `127.0.0.1:4017`、完成 liveliness，并由同一 gateway 完成真实请求后关闭。

同一 `glm-5.3-flash` alias 的实际结果保存在该目录 `provider-requests/gateway-{stream,tool,image}.json`：stream HTTP 200、SSE 8 chunks；tool HTTP 200、`finish_reason=tool_calls`、usage 164/30/194；1×1 PNG image HTTP 200、usage 38/16/54。由此确认本地 auth、callback、api_base 展开、stream/tool/image 接缝均可用；没有测试 fallback 触发，也没有模拟 429。Linux cp312 runtime 仍须按同一 routes/provider-env 合同在官方 sandbox 重新验收。

### stage-a 冻结输入（2026-10-03）

已准备首包消费的 WorkSSD 路径：`runs/iteration14/overnight-20261003/stage-a/support/gateway-routes.json` 是公开 alias→有序 deployment ID 列表；`.private/provider-env.json` 是按三条 active chain 过滤的 0600 gateway 环境；`.private/hosted-qianfan-flash.json` 是独立 0600 Hosted credential，metadata 固定主路由 `model=glm-5.3-flash`、`provider=QIANFAN_TOKEN_PLAN`、对应 base URL 和 `api_key`，并保留 `environment.FACTORY26_API_KEY` 供现有 `lab/exp/hosted.py` 合同读取。正文和普通 manifest 不复制这些值。

已核对 `variants/pi-braid-i14-e2e/run.py`：它物化的 run-local 文件名是 `gateway-config.json`，与 helper 的 state 目录、package 的公开 `support/gateway-routes.json` 以及 `.private/provider-env.json` 不冲突；helper 会把最终 config SHA 写入 binding。e2e 入口应继续传入这三个显式路径，不依赖 ambient `FACTORY26_GATEWAY_ROUTES`。
