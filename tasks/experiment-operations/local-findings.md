# 本地启动、终态跟随与证据回收

2026-10-02。调查读取真实 I13-2 记录、当前源码、保全目录中的链接和本机进程表，没有操作远端执行、调用模型或运行测试。新增原始读回归 [investigation.json](../../runs/experiment-operations/20261002/investigation.json)，记录读取时点、来源 SHA 和进程表响应。当前运行身份来自原件，不把保存的 phase 或 PID 当作实时事实。

## 已有能力与手工拼接

`arc_matrix.build` 已校验冻结题目、包身份和运行资源；`lab.plan` 冻结实际 controller 源码/依赖；`lab.run` 持有 attempt、Docker endpoint、进程及存储生命周期；`lab.wait` 能用持久事件等待终态。`local_monitor` 已有输出目录锁、scheduler、provider 连续观察和通知去重。新方案应直接复用这些能力。

I13-2 的 [prepare-recipe-r2.py](../../runs/iteration13/i13-2-20261001/prepare-recipe-r2.py) 仍逐题调用 `build`，再手工拼接 jobs、资源 argv、来源标签和 run labels。[active-matrix.json](../../runs/iteration13/i13-2-20261001/revision2/active-matrix.json) 另外列出 experiment/source/Python/两条 run；[background-launch.json](../../runs/iteration13/i13-2-20261001/revision2/background-launch.json) 再保存 follower 和 monitor 的进程/源码身份。实验运行记录已经掌握这些事实，但没有一个已有入口负责把启动结果交给两类跟随者，并在其中一项失败时准确指出缺口。

`lab.run.start(background=True)` 目前返回 experiment 与新 PID，不等待控制器登记、attempt 绑定或采集接收。PID 回执证明发起了子进程，不能证明实验和监控已经就绪。控制器事件与当前状态已经提供后续确认依据，无需重新实现实验运行器。

## 终态重放不能从原目录接续

[follow-batch.py](../../runs/iteration13/i13-2-20261001/revision2/follow-batch.py) 第 19 行以 `exist_ok=False` 建立每条来源 run 的重放目录，而且位于 `try` 外；第 66–75 行的 `observed` 只存在于进程内。重新运行时，`lab.wait` 会再次交付现有终态，已经有输出目录的来源随即失败。当前实现偏向中止，没有证据表明它已经重复收费；人为换目录/新建 journal 才会绕过原有 pending 和远端身份。

脚本第 29–33 行按 case 重写 model、硬编码费用和这轮名称，第 35–39 行直接操作 `Controller._competition_locked`。这些是同一组件内部协调和实验配方事实，被每轮脚本再次实现。第 25 行保留 runner exit0、result completed、应用已发布三项门槛，应迁入稳定入口并保持，不能为让流程自动跑通而放宽。

最小改造是按“来源 run + 冻结应用身份 + 本次重放授权”持久绑定同一目录与官网 journal。重入先读既有 package/prepare/submission/run；已启动只继续采集，pending 只做只读核对，需要再评分则另建明确授权的新操作。终态失败与重放失败各自保留；不能把两个都概括为 batch-completion。

## Mac 进程身份判断有已确认缺陷

[lab/control.py](../../lab/control.py) 第 17–34 行仅从 Linux `/proc` 读 boot ID 和出生身份。Mac 上保存值与当前查询值都为 null，`owner_state` 因空值相等返回 alive。主线对真实 preservation 中的旧控制器 PID 98966，以及首轮 experiment 的 PID 15711 执行只读查询：两者 `ps` 均 exit1、没有进程，但 `owner_state` 都返回 alive；当前 r2 PID 93077 的 `ps` 确认存在，但旧 null 记录仍不能证明出生身份。

相同裸比较还在 `lab/run.py:137` 的 retry 分配、`lab/__main__.py:403–405` 的 reconcile 以及 `417–420` 的 cleanup 门禁中；`lab.status`、`lab.wait`、control send/wait 又消费 owner_state。只加一个空值条件或者只让 Mac 开始返回非空都不足以修完整：旧记录的未知身份不能因此放行 cleanup/重试。

建议在现有进程控制模块统一解释身份：确认为同机且 PID 不存在是 lost；存在但缺可比较出生依据为 unknown；非空且匹配才是 alive。Linux 与 Mac 各自取得原生身份，旧记录原样保留。现有 socket 的 controller_id 可另外支持旧控制器身份取证，不把当前 PID 出生时间回填成历史事实。unknown 不允许强制接管或清理。没有当前运行必须立即修复才能继续的证据，按本阶段方案进入开工复核。

## 回收混用了冻结输入与输出保全的约束

`lab.records.inventory` 为输入冻结设计，要求每个链接解析后仍在 snapshot 根下；`Workspace.recover` 却在 helper `/transfer/official-generation` 上用同一逻辑保全输出，后续又使用 `tarfile` 的 data filter 解包。这会让真实生成产生的链接阻断整个证据回收。

首轮两个真实 run 的 [回收原件](../../runs/iteration13/i13-2-20261001/transport-finalization/observation.json) 都保存 `link points outside snapshot`。此前任务仅提出挂载视角解释，本次读取其保全来源补齐了两个不同事实：

| 来源 | 保存的链接字面值 | 已知约束 |
| --- | --- | --- |
| Sheet 的 `work/tasks/pr-2/evidence/node_modules` | `/workspace/submission/agent/runtime/node_modules` | 指向执行布局内目录，但 helper/宿主解析视角不同。 |
| GitHub 的 pnpm projects 链接 | `../../../../../../../../../tmp/sqlite-check` | 本来就越出 stage；当时的 [link-layout.json](../../runs/iteration13/i13-2-20261001/preservation/github/link-layout.json) 明记目标不存在。 |

原 [export-frozen-volumes.py](../../runs/iteration13/i13-2-20261001/preservation/export-frozen-volumes.py) 第 6–23 行已靠字符串替换 inventory 及逐链接特例，完成保全。说明重复劳动并非只缺一次路径配置。上述 readlink 来自旧保全来源；本次没有重新读取 r1 失败卷，不能将来源事实冒称该卷的新观测。

建议区分严格的冻结输入清单与输出归档：后者保存链接字面值及缺失/外部目标限制，不跟随外链拷贝内容，不因无法展开依赖链接而丢掉其余原件。安全解包必须拒绝路径穿越和通过链接写出目标目录；外部链接可先保留在未展开原始归档和链接清单中，不能直接对任意归档取消 data filter。可执行恢复只映射有来源证据的容器路径，具体链接目标不在原件时仍报告缺口。首期不得全局放宽 `inventory` 或修改历史 manifest 算法。

## 回收责任重复，且可能遮住生成错误

[Workspace.recover/finish](../../lab/arc_bench/docker_workspace.py) 的正常 runner 返回、runner finally、adapter finally 三处可对未 verified 的同一 stage 发起完整回收。每次 inventory/copy 有 600 秒级传输超时，失败后会覆盖 entry 中当前 error。原件证明最终链接失败；没有完整的每次耗时时间线，不能声称初始 600 秒超时全由某个目录或链接导致。

此外，Runner wrapper 的 recover 异常发生在官方 Runner 解释结果前。adapter 在缺少回收后的入口结果时，可能写出 `Agent entry produced no terminal process result` 或 `Agent generation did not produce a complete application`；这些只是宿主材料不足，不能替代远端原始生成错误。单独 workspace-cleanup 回执虽保留运输错误，消费者仍须跨文件拼接真实失败链。

最小修正应明确一次自动 finalization 的所有者，保存执行容器退出事实后进行有界回收；失败保留卷及原始尝试日志，并完成“执行已结束、归档未完成”的记录。显式补采从这个记录接续。清理始终要求本地保全核对成功，不以新回执覆盖首个生成错误，也不在层层 finally 中重复触发相同耗时动作。

## 反馈边界

上述结论由当前控制流与已保存原件支持；本次没有测得启动/恢复的人类工时，不能给出未经测量的节省比例。后续可用真实历史输入在独占隔离副本中完成准备和安全归档操作，并以原件内容/系统观察独立读回。新控制器身份、脚本持续接管及实际 provider 接续分别在获授权的真实操作中取得证据；无模型 prepare 成功不能代替它们。
