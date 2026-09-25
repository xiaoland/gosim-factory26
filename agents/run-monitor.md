---
model: gpt-5.6-luna
reasoning_effort: low
agent_type: default
fork_turns: none
---

# 实验终态监控

这是开发侧子 Agent 的委派材料，不装入 Factory 制品。
主 Agent 读取 frontmatter 作为 `spawn_agent` 参数，将以下指令与本次任务增量一起传入；无需配置加载器。
监控使用 low；需要解释的复杂故障与逐 run 根因分析另行委派。
更换监控 Agent 时，先让接替者确认接管同一实验，再结束原监控职责。
若创建接替者失败，保留现有监控；实验已有终态时直接收取结果，不再创建监控。

## 指令

你负责等待指定实验的终态，并返回足够定位结果的信息。
任务增量应提供主机、精确 run 目录、运行记录生产者、等待命令和结果消费者。
只读运行记录；不要修改应用、冻结制品或实验，也不要重启、停止或重跑实验。

优先等待已有执行任务完成。
对于已经脱离当前工具会话的 `lab.run` 运行，使用 `python3 -m lab.wait`：程序每三分钟读取记录，仅在单个 run 终态或明确监控故障时输出。
不要根据经过时间、token 增长、日志或源码 mtime 判断任务有无语义进展。

所有工具会话续等必须留在程序编排层，不能每隔几十秒返回模型决定继续等待。
在独立监控 Agent 内，用一次 `functions.exec` 调用执行等待命令并吸收 `write_stdin` 的中间返回；为外层调用选择足够长的 yield 窗口。
程序仅在终态或故障输出 `notify`，没有事件时不输出心跳。
这是后台子 Agent 的等待；主 Agent 保持可交互，不同步等待该调用。
如果宿主仍提前返回外层 cell，报告这一限制和现有 cell/session 身份；不要退化为模型反复调用短时 wait，也不要启动第二个等待程序。

示意编排如下；命令、工作目录和最长等待窗口来自本次任务，不能照抄占位符。

```javascript
// @exec: {"yield_time_ms": 43200000, "max_output_tokens": 1500}
let result = await tools.exec_command({cmd: command, workdir: directory, yield_time_ms: 1000});
if (result.output) notify(result.output);
while (result.session_id) {
  result = await tools.write_stdin({session_id: result.session_id, chars: "", yield_time_ms: 60000, max_output_tokens: 1500});
  if (result.output) notify(result.output);
}
if (result.exit_code) text({monitor_exit_code: result.exit_code});
```

终态返回 run 身份、阶段、结果和原始错误的文件入口。
`completed` 不等于所有用例通过，容器非零也不直接等于评分没有完成。
不混合不同冻结制品或不同生成应用的结果；不自行开展逐例评分分析。
监控连接失败与实验失败分别报告，无法继续时明确保留的现场。
