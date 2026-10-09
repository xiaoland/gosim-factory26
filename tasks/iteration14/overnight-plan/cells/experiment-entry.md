# I14 e2e→reviewer 实施接缝

本页只定义可交给实施 owner 的输入、输出和判定门槛；不启动模型、prepare、评分或源码修改。主实验顺序、机会数和费用仍以[主设计](../design.md)为准。

## 已核实的起点

`pi-braid-i14-e2e` 已把 `e2e`、`agent-browser`、`arc-bench` 等技能作为冻结包内独立入口发现：`main.py` 的 `MAIN_SKILLS`、`run.py` 的 `skills/<name>/SKILL.md` symlink、profile 的 `skillPath` 和角色材料共同构成发现链；技能正文没有内联进 prompt。`tools/e2e.config.ts` 要求显式应用 URL、模型 API、wire model 和 key，且固定 `workers=1`、`retries=0`、trace/cache 规则。tester-army 的真实一次 Flash explore 已有 `runs/iteration14/tester-e2e/ai-one-step/` 证据，但它只是一次保存动作探索，不是 GitHub 验收。

历史 e2e 运行有 10 条成功 assistant/toolUse、实际 Flash 路由和 2 GiB cgroup 证据（`tasks/iteration14/dx-resume/{execution,startup-blockers}.md`），只能证明模型/工具运行接线和资源采样曾成功；没有应用发布、公开需求覆盖或完整评分证据。涉及已清理运行的路径只代表历史回执，原始现场已删除，不能作为当前可恢复 seed。因此实施入口必须把“技能可发现”“工具被实际采用”“候选可验收”分成三项字段，不能以前两项代替第三项。

这里要区分两个身份：Braid 的 typed `ReviewRequest`/`review context` 是另一条产品对象能力，不是本次 variant 必须改造的前提；`pi-braid-i14-reviewer` 当前实际数据流是 `requirements_dir` → `run.py:generate` → `work/application` → `initialize_repository(app)` → `braid-request.json` → Braid local。它没有现成的应用 seed 参数，当前 host/Git reviewer 操作也没有证明 native reviewer 已启动或 checkout 对应可运行应用。空应用初始化或仅有 source checkout不满足本轮 seed条件。

## 最窄的 reviewer seed 接口

最小接缝是给 `variants/pi-braid-i14-reviewer/build.py` 增加可选 `--application-seed` 输入（已发布 A 目录或根部含 `application-manifest.json`、`application/` 的冻结 ZIP），把校验后的 seed 固定进包内 `seed/`；标准 `main.py` 仅在这个包内固定目录存在时显式注入 `--application-seed <package>/seed`，不读取 ambient 外部路径。`run.py` 的同名参数保留给受控开发/回放入口。复用 manifest 的 `application_id`、`source_identity`、`commit`、`requirements` inventory 和应用文件 SHA。不要新建含 `service_url`、PID、runtime binary 的平行 manifest。入口定位在 `generate` 解析 `requirements_dir` 后、创建 `work/application` 前：读取并校验 A manifest，调用现有 `copy_application(A/application, work/application)`，再按现有顺序 `initialize_repository(app)`；**随后仅在 seed mode 对复制出的确切应用文件执行 `git add -A` 和一次初始 commit，并回读该 commit/tree 与文件 inventory**。当前 `initialize_repository` 只有 `git init + commit --allow-empty`，不会提交复制文件；普通空应用模式继续保持原语义。这样新 Braid 本地仓库从 A 的文件快照重新初始化，A 的 `.git`、`.braid`、`node_modules` 不被带入，A 保持不可写。

该 seed 输入只需补一份本次审阅的关联回执（例如 `application-seed.json`），记录 A manifest SHA、实际复制目录和公开需求目录 SHA。服务由这次 reviewer 副本单独启动，使用新的临时数据目录/端口；不能复用或修改 A 的服务、数据库、浏览器 profile。服务 URL、PID、runtime binary 是 reviewer 运行证据，写入本次 run metadata，不是 A manifest 的必填字段。

运行控制面消费的报告路径为 `<run>/work/audit-report.json`，终态回收为 `<run>/audit-report.json`；schema 为 `{schema_version:1, mode:"seed-audit", a_manifest_sha256, requirements_sha256, candidate_commit, status:"complete", unauthorized_changes:false, changed_files:[], authorized_files:[], findings:[...]}`。每个 finding 至少有 `category`、`evidence`；`mechanical` 还必须有 `reproduction` 或 `data_flow`、`verification`、`fix_commit`，且 `fix_commit` 等于 candidate commit。实际机械闭环由独立 LLM 审阅和实施检查负责，程序只核对身份、字段和显式变更范围；存在未授权变更时保留证据、不发布。缺失或不匹配写 `<run>/audit-status.json` 的 `evidence_incomplete`，保全工作区，不进入 delivery/publish，也不自动重跑。

若没有可消费的既有应用 manifest，实施 owner 才需新增上述单一 `--application-seed` 接口及复制/初始化插入点；不能把普通 `requirements_dir` 或空 `work/application` 误称为 seed。

reviewer 输入使用现有 A manifest 的最小字段：

| 字段 | 机器条件 |
| --- | --- |
| `application_id`、应用文件 SHA、`source_identity`/`commit` | `application_id`、文件 inventory 和 `source_identity` 非空且与 A manifest、复制后的 reviewer tree 实际读回一致；若 A manifest 的 `commit` 为空，绑定 snapshot/files inventory，不把空 commit 当错误；有 commit 则保留并核对该身份。A 不可变。 |
| `requirements` inventory、需求来源/版本 | 能与本轮公开 GitHub 需求目录的冻结 SHA 对照；不同 SHA（例如 `948092…` 与旧 I14 输入）不作比较。 |
| `delivery_kind`、`application-manifest.json` 状态 | 必须是已发布应用交付；prepare、暂停、设施失败或单纯模型响应不构成 seed。 |

入口在 reviewer 真正接手前执行 `seed_gate`：manifest/文件复制身份不符或 A 不是 published 时返回 `seed_unusable`，不把空目录称为审阅候选；该 gate 必须发生在 `load_delivery`、`publish_application`、`deliver` 和 `publish_history(preview=True)` 之前，A 只能存在于本次 run 的 `work/application`，不能提前写入平台交付根。seed mode 的 request 文本必须明确“这是独立公开需求审阅；只修公开需求明确、实际复现或数据流闭合的机械缺陷；语义/证据不足保留；不从零开发、不扩展产品功能、不替换完整生成团队”。审阅者只查验并提交报告，实施者只根据合格机械项产生 B；不能只换 prompt 后继续沿用默认从零脚手架/基础 PR 团队职责。服务健康、端口、浏览器数据和 runtime 证据分别属于本次 reviewer 副本；若某项证据缺失，只按用途报告（例如不能证明浏览器复现、不能独立评分或不能归因），不自动阻止与该证据无关的应用交付。reviewer 输出必须带本次 run identity、A manifest SHA、公开需求 digest、观察/证据路径、结论和逐项 `mechanical|semantic|insufficient` 分类；无需假定改动 Braid `ReviewRequest` context/conclude。

若存在合格机械项，实施 owner 在 A 的独立可写副本产生 B；A 的包、source ref、服务数据和评分证据保持不变。B 只有在新 artifact/source/tree、A→B base、修改收据、同一公开需求 digest、重新 build/health/browser 回执齐全时才可冻结；将 B 交给新的 Hosted seed-audit run，复用首轮 Linux/gateway 接线，由该新 run 直接进入平台 template 并取得完整评分，已有有效 B 分数不再 replay。没有合格修复时只产完整 audit 报告并让 Harness 正常结束，不造异常或空壳；平台若 `FAILED` 或尝试后续测试，原样保存其状态和费用未知，不靠 generic 状态认定审阅完成或应用零分。缺报告或修复证据是 `evidence_incomplete` 并停止，不自动重跑；若用户要求绝不开始评测，当前 venue 还需另行用户决定，本轮未作此要求。报告回收沿已有日志的有界摘要和 workspace ZIP 接缝。任何 hidden evaluator 反馈、分数猜测或 Sheet 个案都不能进入 reviewer 输入。

## GitHub 公共需求验收与修复规则

验收输入只有冻结的 GitHub 公开需求和实际候选 A/B。对每条公开要求记录 `requirement_id → action sequence → expected observable state → observed state → evidence`，证据引用候选身份、服务/数据身份和截图/日志；只读技能、Issue 或 PR 不算应用成果。应用必须完成公开需求驱动的操作链，包含失败后的状态收口；e2e report 的退出码和 artifact 也需保存。生成完成、应用发布、官网完整评分、e2e 实际采用、OOM/cgroup 证据分别记录；缺少后两类辅助证据只将对应机制标为 `not-observed`/`unknown`，不能否认已发布应用或完整分数。官网测试 `FAILED` 归应用评分失败，不自动归为生成设施失败；只有有具体生成/运输/资源原件时才记 `infrastructure`。

只有同时满足以下条件才允许自动机械修复：公开要求或维护不变量明确规定结果；在 A 上有实际复现，或有可闭合的数据流/操作证据把失败与修复范围连起来；修复后相同操作链得到要求状态；改动不引入新的产品解释。漏传确定参数、未保留既有状态、引用未迁移、确定失败分支未收口属于候选类别，但不能从 Sheet F1–F5 推导 GitHub 缺陷。语义争议、需求不完整、无法复现且数据流也不能闭合、多个合理解释或只有低分/“更合理”判断时，结论为 `semantic` 或 `insufficient`，保留原行为和缺口。

## 三次机会的机器触发事实

机会余额按[主设计](../design.md)的总剩余机会串行消费；独立评分不消费机会，fallback 只在同一请求级路由内切换，不新建 Lab attempt/native session。若前序重启或恢复已消费机会，后续不得把“第三阶段”当作固定第三次，而要依据记录的 `opportunity_balance` 判定是否还能进入下一次模型机会。

1. **机会一：Flash/e2e。** 仅当输入需求 digest、variant/package/source/binary、路由和存储身份全锁定时进入。生成完成且 A freeze manifest 完整，应用交付即成立；在此基础上独立官网评分另记 `score=complete|failed|not-observed`，e2e 实际采用和 OOM/cgroup 证据各自记 `observed|not-observed|unknown`。只有模型响应、技能读取、工具活动、prepare 完成而没有生成/发布终态时，才是 `incomplete`；资源/transport/OOM 等有具体生成原件时标为 `infrastructure`，按主设计的窄修复/接续条件处理并从总余额扣除实际已用机会。
2. **机会二：独立 Hosted seed audit。** 只有 `A.freeze_status=complete`、`A.requirements_digest` 等于本轮输入、seed gate 通过、reviewer 副本责任/session/checkout 身份独立且观察引用 A 的真实服务/数据时进入。`mechanical` 且验证通过才生成 B；B 由新的 Hosted run 直接交付 template 并评分。全为 `semantic`/`insufficient` 时保留 A 并产 audit 报告；seed gate 或报告/修复证据失败时为 `evidence_incomplete`，停止且不自动重跑。
3. **机会三：择一机制复验。** 只有前两项已给出可解释终态（A/B 完整评分或明确无合格修复）、仍有一个具体未解机制、同一需求/根模型/共同材料/资源和供应商条件可锁定时选择一个对照：移除 e2e、保留 e2e 加 reviewer，或复验已由实际噪声支持的 cleaner。若前序是设施失败、输入身份不一致、评分未闭环或原因未知，触发事实为 `blocked_by_evidence`，不凑第三次、不自动换模型追分。

每个机会的状态机应保存 `opportunity_balance_before/after`、`generation_status`、`application_status`、`score_status`、`e2e_adoption`、`oom_evidence`、`eligibility_facts`、`terminal_class`、候选 manifest/score 身份和下一分支原因；这使“完整应用”“完整评分”“工具未观察到”“OOM证据未知”“设施失败”“未具备评分证据”不可互换。
