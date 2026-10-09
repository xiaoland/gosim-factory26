# 旧 checkpoint 恢复

本页只解释原冻结 lab.exp 执行器的恢复入口。当前 Lab run 使用 [restart](../recovery.md)，没有 checkpoint、recover 或 prepare 命令。

<a id="当前-checkpointprepare-与停止门控"></a>
## 当前 checkpoint/prepare 与停止门控

旧 checkpoint 由原域权威关闭真实登记写者并取得 capture 证明。普通应用 ZIP、Git 备份或终态内容复制不具备相同身份；缺少 Git/native、连续停写或定义引用时保留 partial，不能用后来取得的证明追认旧快照。

```sh
python3 -m lab.exp status EXPERIMENT
python3 -m lab.exp checkpoint RUN ATTEMPT --directory CHECKPOINT --request-id CAPTURE
python3 -m lab.exp recover CHECKPOINT --intent RECOVERY_INTENT --environment PROFILE \
  --directory DERIVED --job JOB --request-id REPAIR
```

Recover 默认准备材料，`--execute` 才请求派生 attempt；query、continue 和 abort 使用同一 request。操作与重入门控见[执行合同](../../../lab/exp/execution.md#检查点与显式恢复操作)，文件 schema、定义依赖和完整性边界见[制品合同](../../../lab/exp/artifacts.md#检查点与准备)。

<a id="旧-schema34-checkpoint-与-prepared-合同"></a>
## 旧 schema3/4 checkpoint 与 prepared 合同

旧 Hosted 终态材料只有在终态 GET、终态后的完整 workspace 导出、哈希、execution/attempt 和 logical-root/definition 都可核对时，才可按 `legacy-terminal-export` 导入；来源仍标为 partial，不宣称 managed writer closure。未知或活动写者不能按故障重跑。

Prepared 消费不可变来源和原定义，不因后来更新的 runtime 自动升级。跨版本 patch 必须有精确哈希绑定；目标 OS、architecture、逻辑路径与原生身份仍按来源合同核对。不完整材料可以用于独立应用分析或评分，但不能称为完整原生会话恢复。

历史来源的具体命令、输运错误、一次性接续和修复回执从所属记录或 Git 历史查阅。不要以旧 packet 的计划启动新模型运行。
