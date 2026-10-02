# 截至 2026-10-02 的结果对账与今晚判别项

本页是只读调查结果，服务于今晚实验设计；没有启动模型、prepare、恢复、评分或 Factory/Braid 测试。状态以最新回执为准，旧 packet 中较早的动态截面不覆盖后续终态。

## 先回答“过去一天只有一个完整评分”

在“本轮已登记实验”的过去 24 小时口径下成立；这不是对平台全球结果的断言。唯一可作为完整官方结果的是 I13-2 Flash/Sheet：官网 run `f16834f58674`、submission `e69e9764310c`，生成和评测均 `completed`，74/100（74 通过、26 失败）。本地保存的官方 `status.json` 还给出 `run_duration_seconds=10115`、`feature_implemented_count=11`、`feature_total_count=24`、`evaluation_started_at=null`、`tests=[]`、`node_states={}`；`feature=11/24` 是另一统计口径，不能把 26 个失败直接对应到下面的五个缺陷。证据入口是 `runs/iteration13/i13-2-20261001/hosted-sheet-r2/monitor/20261001T174303.462955Z/f16834f58674/status.json`、`collection.json` 及 `tasks/iteration13/i13-2/flash-sheet-score-analysis/{packet,findings}.md`。

| 运行 | 观察到的终态 | 能否算完整评分 | 不能混入评分的原因 |
| --- | --- | --- | --- |
| I13 Flash/Sheet `f16834f58674` | 官网生成+评测完成，74/100 | 是 | 唯一完整结果 |
| I13 Flash/GitHub `7e8ec62670df` | 后续因 ARC 余额耗尽取得 72 条 HTTP 402 `insufficient_balance`，运行被取消并保全 | 否 | 没有评测终态；前期 RUNNING 只是阶段状态 |
| I13 GLM/GitHub `a94a67b4b3d85b` | 真实 GLM 请求成功，随后源容器停止，Git/Braid/native 选择性保全 | 否 | 生成/评分未完成，保全不是交付 |
| I13 GLM/Sheet `8046cfb0695023` | 真实 GLM/Flash 请求成功，随后源容器停止并保全 | 否 | 生成/评分未完成 |
| I13 官网 GitHub 首轮 `346bc3b51b09` | 生成阶段 `FAILED`，score=0、passed=failed=0、未进入评测；Pi SIGKILL 与同 cgroup OOM 计数增加强相关 | 否 | 设施/生成失败，0 不是有效应用零分 |
| I14 baseline/cleaner/reviewer/e2e | 有的只有 prepare，有的取得模型响应；全局随后暂停 | 否 | 没有完整应用交付和评分；`completed`/模型响应不等于评分 |

I14 的 e2e 确有正向运行证据：`runs/iteration14/dx-resume-20261002/` 关联的系统盘回执记录了 10 条成功 assistant、工具活动、`ZHIPU/GLM-5.3-Flash`、2 GiB cgroup 和 Pi `Max address space unlimited`。这只证明运行与资源边界已接通；不证明工具被正确采用、应用完成或评分。GLM baseline 也有成功 assistant 回执，但同样不是评分。

## 两组 fresh baseline GitHub：暂停前已有进度，但还不能给分

这两组应从 I14 其它分支中单列。它们使用同一份新版 GitHub 需求 `requirements.yaml` SHA256 `9480921cb3b7ffdc5f32cb76011ecc1d5bf9bfbf2cba38e3a092355ac88a54f8`；旧 I14-0 冻结输入和 I13 输入不是同一版，不能把它们当作旧分数的直接对照。两组均由普通 Qwen 路由产生真实模型成功响应，20:48 CST 用户暂停时保留原容器、Braid/native 工作区和精确 attempt 身份。

| fresh baseline | 暂停前已保存的语义进度 | 暂停状态与继续得分的可能性 |
| --- | --- | --- |
| root `glm-5.3`，Braid `20261002-110120-f5e81834`，attempt `attempt-d43144ff7dcff8ea8659d863` | `actual-startup-success.json` 记录 root `glm-5.3`、成员 Flash、`kimi-k3` 等 5 次成功模型响应；`glm-live-readback.json` 的可见 assistant 仍只是在读取 `braid-collaboration` 与 `arc-bench`，12,677 total tokens、error=0。调用次数较多不等于应用语义进度或接近完成。 | `active-bindings.json` 标为 `paused-by-user`，`pause-confirmed-index.json` 有回执，evaluate 尚等待生成 application。原 attempt/container 未被取消或删除；取得用户恢复授权、完成生成并冻结 application 后，理论上可继续进入独立 self-funded 评分。当前没有生成终态或分数。 |
| root `GLM-5.3-Flash`，Braid `20261002-110738-65a19bd7`，attempt `attempt-e0ef27e350f030621a65eb03` | `flash-readback-latest.json` 记录 1 次成功 assistant：读取 `arc-bench` 并发起 `braid issue view 1`，12,733 total tokens、error=0；这表示已开始读需求/工具，语义进度仍很浅。 | 同样 `paused-by-user`、物理 `Paused=true`，evaluate 等待 application。现场可作为继续来源，但不能由 pause 或首条响应推断可得分；须恢复后观察真实生成终态、冻结产物和独立评分。 |

两组的资源回执均为 memory.max=2 GiB、`oom=0`、`oom_kill=0`。这只排除了暂停前已观测的 OOM 计数，不证明应用质量。它们没有触发官网 evaluate attempt；`active-bindings.json` 的 `auto_resume=false` 与用户暂停回执优先于旧的 `running` 字段。

## 顺序接续建议与结果→改进决策树

若取得恢复授权，先续 GLM-5.3 baseline，再决定是否续 Flash。理由仅限执行收益：GLM 已有 5 次成功请求，覆盖 root、成员和 K3 route，恢复后可先验证多路供应商/预算接线是否能从暂停现场继续；这些调用仍只读技能/Issue，没有应用成果证据。两者使用同一新版需求 SHA 和同一冻结包条件，GLM 完成后再续 Flash 能以顺序方式取得根模型分层；不能据此声称 GLM 比 Flash 更接近完成。GLM 若在恢复后出现明确的资源、输运或供应商失败，应保全该错误并转续 Flash，避免把等待时间继续花在不可判别的现场上。

决策树只消费公开需求、生成终态和独立评分，不把 Sheet 的 F1–F5 或隐藏评测反馈传给 GitHub Agent：

```text
续 GLM baseline
├─ 设施/供应商失败（有 HTTP/阶段/资源原错）
│  ├─ 修复运行边界或启用有界 fallback → 保留原 attempt → 再续 Flash
│  └─ 无法闭合身份/输入 → 停止质量比较，先修证据边界
├─ 生成完成、应用可冻结、评分较好
│  ├─ 先续 Flash验证根模型差异
│  └─ 两者均稳定 → reviewer/e2e择一验证独立验收收益
└─ 生成完成但评分较低
   ├─ 先看公开需求对应的生成/验收证据 → 选择 reviewer（发现/修复闭环）
   └─ 若缺连续浏览器证据 → 选择 e2e；不直接堆共同材料
```

“评分较好/较低”应按本轮预先冻结的最低决策阈值定义；没有阈值时只报告分数和证据，不事后改分叉。任何完整生成但评分未知的状态先冻结应用并单独评价；任何设施失败不转成应用零分。

## 74 分目前最可行动的根因

`findings.md` 的五项结论有代码/合同证据，但不是 26 个失败的逐项解释：

1. 第二列筛选覆盖第一列条件。
2. 前端插行/列操作漏传 undo session，后端局部调用正确不能抵消前端接线缺口。
3. 插删列只迁移筛选范围，没有同步迁移条件列。
4. 透视源删除被拒绝后没有关闭确认对话框。
5. 明确单格选择被扩大为已用区域；这是 PR #5 主动写入并在后续交接中保留的错误行为约定，区别于 F1–F4 的实现遗漏。

F1–F4 属于已进入需求/设计但没有完成完整用户操作链的遗漏；F5 是需要重新对照原文裁决的错误决定。真实 Issue/PR 追踪还表明：延后义务没有以完整结果交给消费者 PR，已有的局部测试集合和 ARIA/文案矩阵被当成完整验收。因而当前最强的质量解释是“需求裁决与端到端收口不足”，不是单纯模型等级、cleaner、reset 或 OOM；没有证据量化任何一个因素对 74 分的独立贡献。

## I14 四分支实际在验证的独立假设

| 分支 | 独立假设 | 当前已有证据 | 尚未具备的证据 |
| --- | --- | --- | --- |
| baseline | 干净根成员按原流程能产生可比较的应用质量基线 | I14 曾取得真实模型响应；早期 baseline 另有 GLM 成功回执 | 同一输入下的完整生成、交付、缺陷清单和评分 |
| cleaner | 将 Issue/PR 描述维护、隐藏/解决评论等整理责任移出工作成员，可减少整理成本并保留决定 | cleaner 方案、材料冻结、只读写身份拒绝与恢复准备已验证 | 实际 turn 结束提交、整理耗时/费用、决定遗失或误 hide/resolve 是否下降；不等于直接修复 F1–F4 |
| reviewer | 独立负责人按 GitHub 公开需求和实际候选审查，可能在交付前发现并促成修复 | reviewer 角色/合同和准备包已完成；I13 暴露过局部验收不足 | 一次独立 review 的实际发现、证据对应关系、修复闭环及相对 baseline 的新增成本/收益 |
| e2e | 以真实浏览器操作链和失败后状态核对，可能发现静态验收遗漏的连续状态缺陷 | e2e 已有真实模型/工具活动和资源采样正反馈 | 工具是否被 Agent 实际采用、实际候选覆盖情况、应用完成与独立评分 |

“协作材料/arc-bench 方法”是跨分支的共同条件，不是已经证明有效的第五个对照。I13 中根读取方法、部分平台交付采用，但后续接手和合并判断没有稳定兑现；不能以技能读取次数代替效果证据。

## 运行设施的真实边界问题

用户关于“运行定义、运行数据边界/分离”的直觉有历史证据支持。相关历史缺陷已有修复或接线变更，但本轮仍需用真实运行回执验证，不能把源码/离线修复当作已验收：

- 新 runner 接管 OTLP 后跳过旧 `serve_run`，但资源采样仍由旧路径生产；结果是 e2e 已进入 Braid 却因缺 `resource-latest.json` 等待。模型未失败，运行事实缺生产者。
- prepare、输入输运、execution、native activity、应用产物和官方评分在历史上被外层 `completed` 或单个阶段字段混淆；当前文档已要求分别呈现，但旧记录仍能把 prepare/模型响应误读成完成。
- 大型 workspace 传输与全域 physical admission 共享同一窗口；单容器 export/cp 超时会让全量准入查询超时，未知对象必须阻塞，导致“没有槽位”和“某对象暂时不可读”难区分。
- e2e 曾出现冻结包声明的 Braid SHA 与 `/proc` 实际执行 SHA 不一致。后来核对证明包字节一致、是来源声明错误；这说明运行定义必须绑定实际冻结文件和实际进程身份，不能只信 variant 名或 manifest claim。
- 旧失败中有 300 秒固定大复制超时、存储预留与回传峰值不匹配、暂停/停止/保全边界混用。它们会制造设施失败或延迟，但不能折算成模型质量分。

今晚若继续实验，最低数据边界应是每个 attempt 单独保存：`recipe/input/source SHA`、provider wire ID/endpoint 身份、prepare 终态、execution/native 终态、应用产物身份、独立评分身份和具体错误；任何缺一项都标为未闭环，而不是分数 0。

## 今晚最有价值的少量比较与最低完成标准

主线不应把 baseline 对 cleaner 作为资源不足时的优先比较：cleaner 主要改变协作整理成本，与 I13 已知质量缺陷的因果关系弱。更有信息量的顺序是：先比较 reviewer/e2e 相对根模型的差异；若只能做一条，优先保留同一新版 GitHub 输入下的 reviewer 或 e2e 与一个根模型基线，另一个根模型仅作为质量/供应商层的分层因素。reviewer 要回答独立验收是否发现并促成修复，e2e 要回答真实浏览器连续状态是否揭示遗漏；根模型比较只能说明模型条件差异，不能单独证明机制因果。

Sheet 的 F1–F5 只能作为历史机制例子，不能变成 GitHub 的固定验收清单，也不能把这些实现细节或隐藏评测答案注入赛题 Agent。GitHub 只应依据其公开需求和新鲜生成过程形成验收观察。e2e 只在资源/供应商接通且能保存真实浏览器操作证据时加入，不要把“工具成功响应”当成 e2e 验收。

每条实验最低完成标准：真实 provider 响应；生成终态为 success 或有可诊断具体错误；应用冻结且 SHA 可读；reviewer/e2e 证据必须引用 GitHub 公开需求和实际候选，不预设 Sheet 的缺陷清单；最后再评分并保存官方原始结果。若生成/输运/准入/余额失败，保留原 attempt 和错误，记为设施或供应商未闭环，不重命名为应用零分。

供应商 fallback 是今晚的运行策略，不是质量对照变量：每个已冻结候选在 recipe 中保存首选 wire ID、endpoint、credential mode 和有界 fallback 顺序；只对明确的 429/余额耗尽切换，保存原 HTTP 状态、响应摘要和 request-level route 身份。相同 alias/model 的 fallback 不制造新的 Lab attempt 或 native session；如果 alias/model 改变，则另起显式变体，不能在同一候选中静默改变质量条件。

### 证据入口

- I13 当前矩阵：`tasks/iteration13/experiments.md`、`tasks/iteration13/i13-2/packet.md`
- Flash/Sheet 正式结果：`tasks/iteration13/i13-2/flash-sheet-score-analysis/{packet,findings}.md`
- I14 方法与结果对账：`tasks/iteration14/evidence.md`
- I14 启动卡点与正向运行：`tasks/iteration14/dx-resume/startup-blockers.md`
- I14 当前暂停/恢复边界：`tasks/iteration14/dx-resume/packet.md`、`tasks/iteration14/packet.md`
- fresh baseline 顺序与暂停回执：`tasks/iteration14/baseline-roots/packet.md`、`runs/iteration14/baseline-roots-20261002/{active-bindings.json,actual-startup-success.json,user-pause-20261002/pause-confirmed-index.json}`
