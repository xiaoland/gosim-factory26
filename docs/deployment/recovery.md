# 工作区恢复入口

恢复操作先明确输入、来源身份、当前停止事实及本轮授权。设施修改和模型执行是两个授权范围；已有评分、目录或快照不能自行成为下一次运行请求。

<a id="当前-checkpointprepare-与停止门控"></a>

## 当前 checkpoint、prepare 与停止门控

```sh
python3 -m lab status RUN
python3 -m lab checkpoint RUN ATTEMPT --directory CHECKPOINT --request-id CAPTURE
python3 -m lab recover CHECKPOINT --intent RECOVERY_INTENT --environment PROFILE \
  --directory DERIVED --job JOB --request-id REPAIR
```

Checkpoint 由原域权威停止新增写者、关闭真实登记写者并取得 capture 证明，不要求操作者制作 closure JSON。外层 Local 的已验证终态 SDK child 可作为来源；多个来源需显式 `--source-resource`。来源的 child 身份、外层关系、快照及 Harness member 分开保留，不套用外层路径。非零入口不自动否定可恢复状态，官方 SDK resume 仍不支持。

Recover 缺省只准备选定 job，`--execute` 才请求一个派生 attempt。query/continue/abort 使用同一 request；abort 保留状态、修复 ledger 与 generation，不默认回滚或复活旧 writer。snapshot-copy 消费不可变快照，同域 domain-state 在受管许可内有限修复及原子交接。具体命令、来源停止导入和重入门控归[执行合同](../../lab/exp/execution.md#检查点与显式恢复操作)。

完整 snapshot、checkpoint schema3/4、定义依赖、目标 OS/architecture/runtime/logical-root、修复类别和 acquisition 的合同归[制品与恢复证据](../../lab/exp/artifacts.md#检查点与准备)。普通 workspace ZIP/application/terminal-content-copy 不能补造为 checkpoint；缺 Git/native/连续停写或真实定义引用时保留 partial。未知/pending/live 写者不能按故障重跑，也不能通过后来的证明追认原普通快照。

已发布应用可以独立评价，不必把不完整 checkpoint 当作零分。阶段应用须冻结明确 commit，阶段评分不进入仍在生成的 Agent；模型政策及费用仍由当前配方和授权明确选择。[平台与制品](competition.md)解释当前提交与重放边界。

## 历史来源

[旧冻结恢复、应用重放与监控](history/recovery.md)保存 operation/Competition、旧 ZIP 修复、来源停止和大材料接续的完整原流程及错误。它们只适用于对应冻结执行器和原来源，不作为 schema3 新 writer 的命令推荐。新观察只有一个 owner；status/monitor 只消费其保存事实，不另建旧 collector，详见[执行状态](../../lab/exp/execution.md#查询保存事实)。
