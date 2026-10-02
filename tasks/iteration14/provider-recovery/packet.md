# I14 旧现场逐模型供应商恢复

用户最新指令为“实验DX改进完成了。现在我们继续推进。”本任务消费已授权 I14 热修/恢复范围，只准备共享恢复接线与真实离线反馈；不启动生成、不停止旧源、不创建 Console 或采集器。主线负责配方、宿主准入、冻结和实际 Linux prepare/启动。源码改动限 `scripts/agent_support.py` 与 `submission/recover_completed.py`；后者已有原通知 owner 的未提交改动，本任务保留它们。

cleaner 来源为 `runs/iteration14/cleaner-hidden-context-20261002/stopped-handoff.json`，完整 workspace SHA 为 `abf6ae90c0fc3c8e1b63cca648847777400db808df7c919aa30304fd3b41c82f`。保全原生材料使用 Pi 0.85.1，profile 为 `factory26/glm-5.3-flash` 与 `factory26/glm-5.3`；同一 provider 定义同时包含 Flash、GLM、DeepSeek 与 K3。DX 的新生成拆分 provider 会改变既有 profile/会话身份，因此旧恢复入口主动拒绝。

恢复现在消费相同 `FACTORY26_MODEL_BINDINGS`，使用 Pi 原生的模型级 `baseUrl`、`headers.Authorization` 环境模板及 `samplingParams.model`。provider、native model ID、profile、角色选择、历史及预算模型 ID 保持原值。显式 `route.model_id` 仅改变供应商请求体中的 model 字段，回执 `model_transports` 记录 native provider、native ID、wire ID 与 endpoint。模型 API 限 OpenAI completions/responses；没有新增网关或 Pi 扩展。

当前已获准 Flash 的 wire ID 为 `ZHIPU/GLM-5.3-Flash`，普通 Qwen 的 endpoint/key 环境变量是 `QWEN_BASE_URL`/`QWEN_API_KEY`；K3 使用 `KIMI_BASE_URL`/`KIMI_API_KEY`；其它模型使用 `QWEN_TOKEN_PLAN_BASE_URL`/`QWEN_TOKEN_PLAN_API_KEY`。用户随后明确 DeepSeek 使用 Token Plan 的 `deepseek-v4-flash-0731`；I13 保留 `kimi-k2.7-code`，只切自有 Kimi 供应商。没有把 K2.7 改成 K3。

材料刷新时，对旧未拆分 profile 临时使用 provider 级绑定生成角色与 launcher，随后恢复原 models.json 并最后应用显式逐模型传输；这避免刷新步骤先引入拆分身份。已有拆分身份的材料继续使用原 DX 绑定逻辑。共享 packager 的 refresh/override 互斥门控由主线解除，本任务未修改该文件。

真实离线材料反馈保存于 `runs/iteration14/provider-recovery/cleaner-native-transport/`。`recovery-native-transport.json` 记录原件备份与文件 hash；`readback.json` 记录保全来源、profile、路由与10份未改变的会话 JSONL。`role-settings-readback.json` 核对30份角色/设置文件完全不变。`native-auth-readback.json` 使用保全的实际 Pi ModelRuntime.getAuth/prepareRequest、buildBaseOptions 与 OpenAI.buildHeaders，9条配置最终 Authorization 均匹配所选供应商；回执不保存认证明文。provider 默认 key 与 Flash/Kimi不同的条目也正确被模型 header 覆盖。实际代码编译与 diff 空白检查通过；没有运行 Factory/Braid 测试、smoke 或 probe，也没有网络/模型请求。

Braid 的 `pi.api_key_environment=FACTORY26_API_KEY` 只在 `provider/pi.rs` 注入同名环境变量；显式路由使用三个独立供应商环境变量，因此不被旧 key 覆盖。Pi 对模型 header 做原生环境展开，并在 provider 认证之后合并；OpenAI SDK 再在默认认证之后合并传入 header。原始模型 ID 保持不变，故预算声明和 Braid `local.rs` 的 Profile/model recipe 相等检查继续成立。

cleaner 的直接 `modelRegistry.complete` 路径跳过 streamSimple 的 buildBaseOptions，调用边界现已显式传递 `samplingParams: model.samplingParams`。根与普通成员的 streamSimple 已消费模型级 samplingParams。调用参数由实际 Pi prepareRequest 读回，TypeScript 通过 Node 原生解析；第一次用已有 Linux esbuild 在 Mac 编译因平台不符明确失败，没有安装依赖。所有 variant 的传输覆盖统一放在材料刷新之后，避免 I13 的覆盖依赖刷新复制顺序。实际供应商受理、收费、恢复生命周期、通知送达及完整 Linux prepare 尚未验证，离线配置装配成功不等于运行验收。

I13 Flash/K2.7 的真实原件是 `runs/iteration13/i13-2-20261001/hosted-github-self-funded-r4/final-source/workspace.zip`，SHA 为 `de0f9bfe1af401b49756bf6abfd314fc75641b208f37afa1f70f4d41e826d43c`。独立读取活动 `work/native-homes/pi-glm-fast-*` 的 models.json，4条认证/发送ID装配均正确，保留K2.7。证据在 `runs/iteration14/provider-recovery/i13-flash-k27-retained-transport/`。之前从 GLM GitHub 归档读取的 K3 材料独立保留在 `i13-retained-transport/`，不是本次 Flash 原件，不能用来证明 K2.7。cleaner 的最终0731配置读回在 `native-auth-readback-0731.json`，仍为9条全部匹配。

官网 adapter 目前仅从 deployment 选择一个 FACTORY26/OPENAI key，提交客户端也只发送一个 api_key 表单字段，不能据此传入三路凭据。主线 packager 已增加显式私有 `--model-environment` JSON，文件封入 `.private/model-env.json` 并绑定 manifest。恢复程序在模型绑定之前消费，仅接受 environment 映射、FACTORY26_MODEL_BINDINGS 与其声明的全部凭据变量；拒未知变量、非字符串、缺凭据和链接路径。平台的单一 key 不覆盖这三路显式变量。来源私有 JSON 的600模式由生产端核验；ZIP transport 可能丢失模式，因此消费者在 manifest 验证后恢复目录700、文件600再读取。没有把凭据或其单独hash写入公开回执，也没有新增网关。实际官网展开包的 Linux prepare 由主线完成。

离线操作首次遗漏 Pi home 后明确失败，第二次复制 home 遇到 pulse 的悬空运行时链接；补齐实际认证配置后接续装配成功。来源保全文件未改变。这些是本地材料装配反馈，不用于改写原现场停止/检查点身份，也不替代完整工作区恢复。

DX 发布的 r4 旧来源合同为 `factory26.exp.legacy-source` schema1，使用真实 source_id/execution_instance/backend_identity；停止原件同时保存顶层字段与完整嵌套 source_identity。公开 checkpoint/validate 现在共同消费这个合同，并拒绝给旧来源补造 attempt_id；新执行仍使用原 attempt_id 合同。实际 r4 两份原件身份核对通过。停止 effect/observation、嵌套身份及原件hash的要求保持，内容缺口仍产生 partial，partial 仍不得 prepare。本任务没有把真实原件重建/输运缺口当成完整检查点。

共享源码最终冻结清单在 `runs/iteration14/provider-recovery/final-source-identity.json`；主线/原恢复 owner 应按该四文件hash判断已有候选是否需重新冻结。此处不再继续改动源码，实际 Linux prepare 仍由原 owner 接续。
