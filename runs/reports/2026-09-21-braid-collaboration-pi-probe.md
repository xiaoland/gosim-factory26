# Braid 协作能力：首次真实 Pi 自编辑验收

本次受控验收通过，耗时 122.76 秒。比赛模型为 `deepseek-v4-flash-vision-exp`，核心为 Pi 0.85.1；Braid 源码提交 `63459fc`，Factory 探针提交 `dda8ab1`。SVC 在本探针中关闭，以隔离原生 adapter 与上下文替换行为；活动 Factory variant/config 没有变化。

Agent 在原生 shell 用真实 CLI 创建 comment/reaction，然后自行 hide、delete 和改写根 Issue description。新物理会话从持久对象继续，没有宿主后续消息推动；脚本在运行中使用旧 writer 写入，确认被 fence 且未修改对象。普通自身 comment/reaction 没有产生额外唤醒。

根 Issue 的新原生模型输入包含新标记，且不含旧 description、hidden 或 deleted 正文。主 Agent 独立读取归档输入复核了 3 个携带新标记的替代会话，确认其实际输入包含对应完整 Context，逻辑 group/worktree 保持不变。最终 PR 合入、根 Issue completed、finalization 收敛，冻结交付的 `calc.py` 通过加法的正数、负数和零值断言。

| 观察项 | 结果 |
| --- | --- |
| 逻辑 Agent | 2 个：根 Issue 和 PR |
| 物理 Pi 会话 | 9 个：Issue 6 个、PR 3 个 |
| 上下文重建 | 7 次，全部 applied；其中 3 次是探针刻意触发的 hide/delete/description 编辑 |
| 其它重建原因 | Agent 再次修改 Issue description 1 次；下一次输入前 canonical Context 已变化 3 次 |
| 最终交付 commit | `b67355df623ca5f38f7cfc2cf05c0908eca00dfa` |
| 清理 | 进程正常退出，工作区清理无残留 PID |

9 个物理会话说明替换确实发生，也留下了重建开销的观察值；这个小探针不能证明真实应用生成的收益或成本改善。同类 Issue/PR 并行、失联隔离和运行中 close 已由屏障控制的确定性检查覆盖，本次真实模型没有检验多个同类 Agent 的协作质量。

实现配套验证为 Braid 19 项单元/运行时检查和 1 项真实 CLI 集成全部通过；Factory 81 项检查通过，macOS 跳过 1 项 Linux 专属检查。Clippy 仍被既有 objects/store/context 告警阻塞，不记录为通过。未新增 profile，未清理 SVC Corpus，未启用 provider 原生 sub-agent。

本次不是 ARC-bench 评分实验。真实 Codex 输入、完整 Keep 32 项和多 Agent 生成效果仍待验收。依约在首次实验终态后停止，没有自动重跑、追加 backend 或启动 Keep。

证据：

- [探针判定与交付身份](../integration/20260921-185322-pi-plain-2887cf/check.json)
- [原生会话清单与内容哈希](../integration/20260921-185322-pi-plain-2887cf/native/manifest.json)
- [实际原生准备脚本](../integration/20260921-185322-pi-plain-2887cf/prepare.py)
- [冻结交付代码](../integration/20260921-185322-pi-plain-2887cf/application/calc.py)
- [本地检查与构建日志](../verification/20260921-braid-collaboration/)
