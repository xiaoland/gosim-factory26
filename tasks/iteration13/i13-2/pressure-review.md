# 内存压力判据的独立复核

主线对 `runtime_resources.py` 取得两次独立意见。实现复核发现恢复计数会沿用压力发生前的正常样本，以及历史启动登记读取失败未返回 `resource_deferred`。现已修正：每次压力重新开始恢复计数，只累计之后不同 sample 的低压观察；登记不可读则保存具体错误、保持旧登记并明确延后启动。

另一个争点是：`memory.current` 接近 `memory.max`、inactive file 很多、PSI 很低时，是否必须直接判为 critical。主线短暂增加原始余量小于 128 MiB 的硬门，随后按 advisor 的独立判断撤回。该事实说明下一次分配需要依赖回收，不足以证明必须中止作业；硬门还会驱动有限作业减载，并可能在缓存没有主动下降时持续阻塞。内核在达到 `memory.max` 时先尝试回收，不能把原始 charge 等同不可回收占用。[cgroup v2 内存语义](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files)

保留有界 cache credit、调整后 80%/90% 阈值、PSI、OOM 增量、256 MiB 余量及 128 MiB 启动下限。原始 `charged_headroom` 继续保存。它们是保守估计，不构成“任意下一次分配都不会 OOM”的保证；低 PSI 描述此前的停顿，并不证明未来无压力。[PSI 语义](https://docs.kernel.org/accounting/psi.html)

实际判别沿已授权运行的采样完成：观察 `inactive_file/anon`、`pgscan/pgsteal`、PSI 和 OOM 计数。如果正常启动时缓存下降、匿名内存增加且操作完成，支持回收有效；若持续扫描但回收很少、PSI 或 OOM 增长，才支持进一步收紧折减。原官网现场缺少 `memory.stat`，不能倒推本次折减幅度已经被历史运行验证。本轮不制造 OOM 负载或引入新采集器。

独立复核已核对 [原批准方案](../../experiment-signal-diagnostics/packet.md)、[官网 OOM 记录](../hosted-github-recovery-failure.md)、Python helper 的准入与恢复判据，以及 Braid factory 对压力状态的减载消费。结论仅支持撤回无条件原始余量硬门；实际阈值与缓存折减的效果仍须由获授权运行验收，本次未修改源码或运行测试。
