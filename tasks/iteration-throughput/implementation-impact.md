# Implementation impact handshake

状态：Human 已明确批准开工（2026-09-22）。实现、资格与完整实验在此范围内继续推进。

## 本次会改变什么

```text
Factory repository
├── Pi lifecycle proof
│   ├── extension receipt 收紧
│   ├── 归档保留 terminal/lease 证据
│   └── 分层资格场景
├── Harness capability assembly
│   ├── 删除活动 preset 层
│   ├── 4 variants / 2 Braid profiles / 5 native roles
│   ├── SVC 语义索引与 canonical V&V 装配
│   └── effective manifest + package hash
├── Official execution
│   ├── Competition adapter（新）
│   ├── local-simulation adapter（必要时最小新增）
│   └── hybrid matrix controller
└── tests / task packet / experiment reports

sources/braid repository
├── migration 0007: public assignee login + description
├── GitHub-like create/edit assignee surface
├── Issue/PR/context public projection
├── runtime internal-field hiding
├── exact-one-wake reassignment
└── Pi receipt mode validation

sources/svc repository
└── 不改 Corpus 正文；Factory 只引用 main@393b935 的 canonical paths/hash
```

## 数据、兼容与删除影响

- Braid SQLite 新增 forward-only migration。旧 DB 能打开和归档；缺公开 assignee 的旧活动 request 不跨版本恢复，需要新建运行。
- 活动 `variants/*/preset.json` 路径和 generalist/旧 verification 组合退出 resolver/matrix；历史 run、旧 ZIP 和报告保持只读。
- Runtime JSON/context 不再输出内部 profile id、model/provider、digest、assignment generation 或 session。宿主诊断仍可读取。
- 不引入新外部 Python/Rust 依赖；优先复用现有 SQLite、HTTP client、Pi extension 与 upstream local runner。

## 外部副作用与资源

- 实施和大部分检查在本地完成。Competition 的 GET schema 检查会读取现有登录会话。
- 资格阶段会对三个比赛模型各做最小调用；当前都被 429 `insufficient_quota` 阻断，未产生 usage。额度恢复前不会启动正式生成。
- Runner 资格需要 Docker daemon 和固定官方 image；当前本机 daemon 不可用。只在可固定 image/digest 后构建或拉取，不用主机环境冒充。
- Hosted 阶段预计创建 4 个冻结 submission snapshots，并为 Keep/BookStack 创建最多 8 个 Competition runs；所有写入逐步持久化、无自动重试。Local 会运行对应独立容器作为快速反馈，实际并发受 Meter 限额约束。
- 共享 key 的并发成本无法按 run 精确归因时，明确记录 `unattributed`，不制造估算值。

## 验收证据

1. 无模型 lifecycle 反例先红后绿，三层身份/terminal/lease 对齐。
2. Braid migration、公开 assignee CLI、投影、writer fence、恰一次 wake、同 assignee 真并发通过行为测试。
3. 四 variant effective manifest 只存在批准的差异；runtime 不泄露内部概念；SVC hashes 可复现。
4. 同一 ZIP 通过结构、prepare-only、标准 frontend/backend deploy 和单题资格；`deploy.sh` 不计。
5. Competition fake state machine 覆盖 write-unknown、恢复、cursor 和重启；真实 smoke 使用同一 bytes。
6. 四 variants × 两题均取得带 venue 的完整结果后停下汇报；成绩高低都算实验结果。

## 主要风险与回退点

- model quota 未恢复：源码与无模型资格可完成，真实生成和 score 保持 blocked，不替换模型掩盖失败。
- Competition 缺稳定 identity/history：停止自动 hosted 写入，保留 local 与人工单步，不盲重试。
- Pi 上游不给 observed terminal/lease：该 work-item 保持 unknown/blocked，不在 Braid 猜测终态。
- assignee 投影要求第二套 owner 状态或暴露内部 profile：返回设计；当前证据表明现有单 owner 字段足够。
- official image/digest 无法固定：local 只报告 prepare-only，正式成绩仍以 hosted 为准。

## 提交边界

批准后第一步提交当前设计与预演文档，仅包含 `tasks/iteration-throughput/`。现有无关修改 `tasks/competition-p0/packet.md` 保持在提交外。随后按 [线性实施计划](plan.md)实施；Factory 与 `sources/braid` 分别提交各自归属的变更，`sources/svc` 本轮不提交。
