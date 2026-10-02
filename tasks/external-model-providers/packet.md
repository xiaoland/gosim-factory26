# 自购模型 API 接入调查

状态：用户已授权修复确认属实的 Braid provider 缺陷，并创建项目内 secrets 位置；统一网关与新的模型调用仍未授权。既有实验保持停止。

用户希望用自行购买的 Kimi、GLM、DeepSeek API 组合进行本地开发，保留官方未来五天500额度及正式提交预算。

## 已核实的现状

`local_experiment.py` 只执行外部命令和保存原始 OTLP，不解释模型供应商。`arc_bench_adapter.py` 的 env-file 可以传任意变量，`arc_matrix.py` 命令入口目前为全矩阵选择同一 env-file。各 job 的命令本身可不同。

四个团队 variant 的 `run.py:native_files` 将所有文本模型写入同一 factory26 provider，使用一个 base URL 和 FACTORY26_API_KEY；视觉 provider 可单独配置。成员 profile、内部角色 Markdown 和模型 descriptor 固定实际模型与兼容参数。只替换根模型或 URL 不足以将混合团队分流到不同厂商。

raw 入口已有 endpoint/key 注入，但默认 URL 是官方网关，模型参数来自 raw_models.json，仍需依据目标 API 的实际模型名和协议重新选择。Codex 当前通过 LiteLLM Responses 兼容层接 Chat。

发布的官方 local_submit.py 在 OPENAI_API_KEY 非空时会用该值登录 meter.arc-bench.com；Docker 还会将宿主同名变量覆盖 env-file。自购API运行必须避免把第三方key交给此Meter路径，也不能意外继承官方key。不修改官方评测器，优先在接入边界显式隔离环境，provider独立key只供容器内客户端解析。

## 当前设计讨论

用户纠正：模型接入方案不能以Pi原生多provider为核心，应避免与具体Agent Harness耦合。此前建议不再采用。

已核实Braid现有边界：`provider/factory.rs:materialize_native_home` 为每个新物理会话创建 `<profile.id>-<uuid>` 的home，并复制对应binding.native_template；恢复会话复用原home。Pi设置PI_CODING_AGENT_DIR（不是PI_HOME），Codex设置CODEX_HOME。配置目录隔离不是凭据或网络安全隔离；进程仍继承父环境。不同profile的主会话因此可以采用独立客户端连接配置，不能据此假定同一profile内多模型子代理已经获得独立连接路由。

模型到上游供应商、endpoint和credential的映射应归独立于Pi/Codex/Braid的API接入边界。客户端在各自home内只保留接入该边界所必需的原生配置，实验调度与OTLP仍不解释模型路由。现有mixed profile内同时有DeepSeek、GLM、Kimi及视觉角色，单靠每profile独立home不足以解决其分流。

若采用统一API入口，优先评估已有兼容网关是否覆盖实际购买服务，不自制代理。其部署与计量独立于实验collector。优先候选为已有依赖LiteLLM（当前资源固定1.102.0）；Portkey为文档层面备选。尚未授权实现；需继续与用户讨论接口和模型身份，不能借此引入自动换模型/故障fallback。原生Chat/Responses差异仍由明确的兼容边界处理。

自购运行不得回退官方凭据，官方Meter的OPENAI_API_KEY登录路径需隔离。当前所有模型实验保持停止；无新增API请求或源码修改。

## 统一API调查结论（2026-09-24）

用户确认优先统一API；不能做到时，至少由Braid agent-profile配置模型与提供商。两条路径都应由profile选择provider/model，具体密钥保持外部引用。

LiteLLM官方文档提供Moonshot、Z.AI、DeepSeek接入，统一Chat以及Responses转Chat桥接；故架构可行。当前项目已经依赖1.102.0及局部Responses兼容hook，不能把latest文档当成冻结版本和目标厂商全链路已经验收。上游issue35878仍报告Responses桥接的reasoning参数与namespace/tool_search处理问题；仅凭入口存在不能承诺Codex全部工具语义等价。统一地址与鉴权可实现，推理档位、工具类型、视觉能力等仍须按具体模型保留能力边界。

Braid现有Profile含provider/model/reasoning。Pi适配器实际将provider传入CLI；调查时Codex的thread/start和resume传model，但未消费profile.provider，供应商主要由对应home的原生config决定。已按用户授权在两处传入modelProvider，空provider传null保留原生默认；不新增供应商注册表。配置注释提到llm_providers，但当前Config无该registry实现，不能用注释作实现证据。NativeHome按物理会话隔离已具备。

子代理配置边界：Braid profile管理成员主会话，Pi内部角色仍由variant持有。若采用独立API边界，内部角色可使用同一入口并按模型分流；若直连回退，仍需明确内部角色选择如何绑定provider，不把每个内部角色擅自提升为Braid成员。

依据：
- https://docs.litellm.ai/docs/response_api
- https://docs.litellm.ai/docs/providers/moonshot
- https://docs.litellm.ai/docs/providers/zai
- https://docs.litellm.ai/docs/providers/deepseek
- https://github.com/BerriAI/litellm/issues/35878
- https://portkey.ai/docs/product/ai-gateway/universal-api
- sources/braid/src/config.rs:146、provider/pi.rs:141、provider/codex.rs:307、provider/factory.rs:227。

此次仅查官方资料与本地源码，无模型请求、安装、网关部署或源码修改。

## 本轮实施与核验

用户授权的缺陷属实，已修sources/braid/src/provider/codex.rs两个会话入口，并修正Profile.provider注释及其协议说明。WSL实际冻结Codex0.155.0生成的JSON Schema确认ThreadStartParams和ThreadResumeParams均接受modelProvider字符串或null。没有调用模型。

项目根`.secrets/models.env`已创建，仅含KIMI/GLM/DEEPSEEK的API_KEY、BASE_URL空值；目录700、文件600，git check-ignore确认忽略。没有迁移或读取旧密钥。文件供用户在macOS工作树填写，尚未同步WSL，亦未接入自动加载。官方凭据另用`.secrets/arc-bench.env`，运行文档已改为项目内路径。

WSL隔离编译目录为`/tmp/braid-provider-fix-l0HLxm`，不覆盖现有WSL Braid源码，不更新实验运行二进制。首次offline检查因const-hex未缓存失败；联网获取锁定依赖后`cargo check --locked`成功，19条现有未使用代码等警告，无编译错误。当前不运行Factory自身测试或包smoke，实际模型验收需另行授权；不提交代码。

## 自购凭据实际调用（2026-09-24）

用户填写密钥并明确要求试用，授权本次最小直连调用，不恢复bench。已安全同步到WSL项目`.secrets/models.env`（600），三家`/models`均HTTP200；随后各一次Chat请求均HTTP200、finish=stop、答案391：kimi-k2.7-code总56tokens，glm-5.3-flash总74tokens，deepseek-flash总64tokens，合计194tokens。此次默认推理参数、非流式，无工具调用，不能据此声称流式/工具或统一网关已验收。Kimi的BASE_URL补齐/v1，其余原样。原始请求与脱敏响应在WSL `runs/external-api-check/20260924T041240Z/`，未使用官方ARC端点/凭据，无源码更改。
