# continuation-03：token 成本的根因与可改进项

> 已由[终态 token 复审](token-final-review.md)接续：09:20 是统计起点；终态修正了无头原生续写漏计、子代理与恢复副本口径。下文保留为历史截面。

本轮最优先修的是 **Pi 适配器重复注入同一份 Context**。这已有源码和逐消息证据；无需先压缩工作记忆、换模型或减少成员。其次是已关闭成员被排队通知逐次唤醒时反复新建原生会话，以及等待 bash 作业时继续进行模型轮询。三者会叠加：重复 Context 扩大每次请求，轮询增加请求数，原生重建又增加未缓存输入。

本文只读运行，未改 Harness、应用、评论或执行状态。证据采集始于 **2026-09-28 10:58:30 UTC**；只计 09:20:00.180875 UTC 之后的新 message，不把继承历史重新算成此前发生的调用。Sheet 当时仍生成，数字是截面，不是终局成本。

## 统计边界与可复现入口

原始路径位于 WSL `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/`：

- GitHub：`pi-braid--hackathon--github-88884da4b94a0f/workspace/official-generation/template/.factory26/20260928-030347-78b10c07/`。
- Sheet：`pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation/template/.factory26/20260928-025746-66feadac/`。

[采集脚本](../packet.md)从 `work/native-homes/**/*.jsonl` 读取实际原生会话，使用 session header ID、message ID、timestamp 去重；只累计 message 上的 usage 一次。GH 完成后的副本不会再次计费。保留[压缩快照](token-deep-03/snapshot.json.gz)、[聚合脚本](../packet.md)、[逐会话与工具定位](../packet.md)。聚合复用 `lab.analysis.native_profile.union_ms`，执行 `python3 tasks/braid-product-reaudit/cells/token-deep-03/analyze.py` 可复现。SQLite 以只读模式读取；活跃文件依次采集，非全系统事务快照，因此不以差几个事件推断丢失。

|题目／模型|有 usage 的响应|未缓存 input|output|其中 reasoning|cacheRead|
|---|---:|---:|---:|---:|---:|
|GitHub GLM|370|616,847|108,090|49,550|29,216,960|
|GitHub DeepSeek|59|75,456|30,009|15,162|2,551,168|
|Sheet GLM|734|2,000,360|232,513|102,904|77,586,176|
|Sheet DeepSeek|2,527|3,020,274|1,234,433|727,808|356,087,424|

output 已包含 reasoning，不能再加一次。所有 cacheWrite=0；usage 内 cost=0 是当前记录值，不能视为免费。没有核实模型路由的实际账单单价，本文不给金额，也不把 433.67M Sheet cacheRead 当成同价的未缓存 input。

Pi timing 中 GH 有 429 个 request_start 与 429 个 message_end；Sheet 为 3,266 与 3,261。它们是被 instrumentation 观察到的请求与完成，不证明覆盖底层重试的完整网络次数。请求区间相加为 GH 66.0 分钟、Sheet 300.9 分钟，重叠区间并集为 42.6、93.8 分钟；并发使相加值大于墙钟，不能称为串行耗时。此处不把等待工具、启动和归档时间混入模型请求时间。

## 1. 已证缺陷：同一 Context 在同一会话里不断追加

`sources/braid/src/provider/pi.rs` 的 `inject_context` 将完整文本保存到 `state.context`；`start_turn` 第 384—388 行每次把它拼到新 user message 前。prompt 成功后没有清空，因而后续普通通知再次带上初始 Context。源码行为与真实 JSONL 一致，不能用“前缀缓存命中”解释成没有重复输入。

按同一 session 内、`请处理` 之前完整前缀的 SHA256 完全一致计算，Sheet 重复追加 **69 份、1,990,817 字符**；GH **7 份、131,779 字符**。这只统计可严格去重的原文，未把近似重复计入。

|会话|同一前缀的出现次数|每份字符|直接证据|
|---|---:|---:|---|
|Sheet Issue5，`01a0e750-f3de-71e1-9c6d-a7d4aac8f334`|14|58,247|JSONL 第4、156、187、205、217行等|
|Sheet 根 Issue1，`01a0e750-f3cb-7190-89fd-06143726d5b6`|41|18,266|第4、80、92、102、106行等|
|Sheet Issue4，`01a0e76b-1650-7003-a479-890c7e001d47`|11|26,923|第4、51、63、90、98行等|

完整路径在 aggregate 的 `repeated_context_prefixes`；文件名都以对应 session ID 结尾。Issue5 的第155行请求 prompt 为113,253 token，第156行只有新增 user Context，第157行变成141,017，增加27,764；前一个 assistant output 仅129。下一个同类边界149,211→176,955，增加27,744，前 output109。这证明增长来自新追加的数据，而不是统计重算已有缓存。根会话对应边界每次约增加9.15k token，加上前一个输出。

Issue5 的单请求输入规模从37,491增长到726,452；该会话452次响应，input577,779、output196,121、cache162,894,080。它同时实际完成了跨表 undo 修正与验证，因此不能把整个会话判为浪费；这里能直接消除的是适配器制造的重复副本。

**最小修复建议**：把 `state.context` 当作待注入数据，只有首次 prompt 被原生端确认接受后才清空；失败、未接受与 Deferred 必须保留，新 session/reset 必须重新注入。不要在发请求前 `take()` 后遇错丢失，也不要删除原生历史中的初始 Context。恢复已有原生 session 已清空 state.context，需维持其语义。验收看真实同一 session 的第二个普通通知仅含增量引用；新 session 首次通知仍含完整当前 Context。已有注入数据不靠本次改动自动回收。

**收益量级**：固定实际已观察到的后续响应数，以 Issue5 每份重复仅20k token、根每份仅7k估算（均低于上述实测增量），两会话分别有2,154和3,435次“重复副本被后续请求携带”，合计约 **67.1M prompt token 处理量**。这是明确假设下的保守量级情景，不是严格反事实节省或金额；模型动作、缓存边界和上下文压缩可能随修复改变。也不能再与下文轮询节省简单相加，因为范围重叠。

## 2. 已关闭成员的逐条唤醒与完整重建

Sheet 105个有新 usage 的原生 session 中，95个首轮为 `terminal_contact`；这些 session 合计1,771响应、2.847M input、0.785M output、105.30M cache。**terminal_contact 并不等于无价值**：Issue6 在这种会话里补齐了实际检查、Issue3在结构变化后做了有依据的CSV复验。不能通过禁止联系已关闭成员来省成本。

但独立于语义判断，当前机制确有可避免的完整重建：`group/dispatch.rs::reactivate_work_item_agent` 调用 `sessions.start`；`store/mod.rs::complete_work_item_reactivation` 把旧 sleeping/idle session 标成 replaced，再 INSERT 新 session。`sleep_closed_idle_agent` 判断可睡眠时又明确排除待处理 `direct_contact`，使剩余联系能够再次经过唤醒路径。本轮 Issue3有40 session但仅13个Context revision，Issue6为23/6，Issue7为22/10。

三个可以人工确认的低收益样本都属于 Issue6，Context revision完全相同 `6b6d0319…d5500`：

|新 session|唤醒内容|原生动作与最终结论|input / output / cache|
|---|---|---|---:|
|`01a0e78b-4cdc-7651-b2e0-205604a9a5e6`，10:24|Issue5 comment260|第5行读thread，第7行确认后续#287/#296已经处理、无需动作|32,422 / 2,236 / 16,768|
|`01a0e790-7d5e-7643-9387-f5d77180c60e`，10:30|Issue5 comment268|第5行读thread及Issue6，第8行明确不回复、无待办|33,937 / 1,519 / 16,768|
|`01a0e795-e18c-731a-ade6-ad14546d1556`，10:35|Issue5 comment271|第5行读同thread及Issue6，第8行确认#304早已处理，无需动作|34,739 / 1,922 / 16,768|

三次共 **101,098 input、5,677 output、50,304 cache**，没有代码或评论写入。它们不是同一消息被递归计数，而是不同时间、不同原生session的真实工作。第二、三条读到的长thread已经包含更晚的确认，随后仍逐条处理旧通知。

**建议顺序**：先把已有待处理、属于同一收件成员的联系沿现有批次一起交付；已接受输入和未接受输入必须保持区别。再核实在身份、指令与 Context revision不变时能否恢复原生session，只有确需重建时才新建。保留原消息引用和逐条投递收据，不按“closed”“无用”等语义自动丢弃。三样本中不能宣称全部101k都可免除——至少还需一次读取判断；但批量与复用可避免多份初始输入和重复整串读取。应以真实投递及终态收敛核实，不单按 session 数减少验收。

## 3. 等待路径继续烧模型，且与 Context 膨胀相乘

按“该 assistant 仅发 bash 轮询命令，没有安装、git、braid、curl、进程修改等动作”的保守规则筛选，Sheet有 **598次候选轮询响应**，关联 input218,749、output125,436、cache102,191,808；GH为57次、24,842 / 6,305 / 4,407,296。规则及每个命令保存在 `analyze.py` 与 aggregate 的 `poll_candidates`，它们是待优化集合，不是假定100%可删的浪费账单。

Issue5单会话有117次这样的响应，携带51.83M cache，约占其cache的31.8%。例如反复 `sleep 29; grep ... log || tail ...`；同一条pr19完整检查轮询命令出现15次。Sheet另一个会话14次执行 `sleep 29; grep -c "✓" /tmp/req5-runsh-db23b1f.log; tail -2 ...`。检查真实运行有价值，但每约半分钟让模型再次判断“仍在运行”没有等量收益。

本轮全部11次 `subagent_wait`（Sheet9、GH2）都返回没有对应任务；其中对 `bg001` 的等待明确回复它是 Background Bash，而非子代理。工具结果已提示 bash 完成会自动发消息、等待时可结束响应、不要再造 sleep-and-poll job，随后仍有轮询。因此再次增加同样提示的收益有限，应优先核实并统一现有 bash 完成事件、所有权与等待入口，而非新增监控Agent。若结束响应会导致已关闭成员原生session被替换，后台作业的完成事件归属必须与第2项一起检查，不能直接命令模型停止轮询后丢失结果。

这批数据未发现新的真实 native subagent 调用或子会话usage；`subagent_wait`使用量不能作为子代理利用率。这里的并行主要来自Braid工作项成员。不能据此评价更早vision子代理的净价值，更不能建议一概删除子代理。

## 4. 重复读取和大输出：收益次于上面两项

Sheet新轨迹含859次 `braid comment/issue/pr view` 命令；Issue3 view108次、Issue7 view74次。工具文本输出共5.37M字符，其中按全文SHA256严格相同、长度超过500字符的额外重复124份、436,554字符。跨成员读取同一契约可能必要，这个数不是可全删的额度。

Issue6的 `comment view 271 --thread` 返回37,247字符，内容覆盖多个后续结论；同一大型thread被迟到通知反复触发，优先处理投递批次和会话复用，比要求模型每次猜着用 `head` 更可靠。模型应按未决问题引用具体评论，thread仍保留为补背景的入口；不能裁掉关键上下文来省token。

两条有明确低价值内容的输出：

- Sheet session `01a0e799-67ff-73ee-86f1-4aebeeef9e07` 第27行，10:41:07：尝试从持久工作区到 `/tmp` 用 `cp -al` 复用 node_modules，产生4,499行、559KB `Invalid cross-device link`；工具已截断，但仍把51,388字符送入模型。后续仍需正常安装/复制。这不是网络慢，而是跨文件系统硬链接方案本身不成立。复用依赖时先看设备边界，或直接使用已支持的普通复制/安装路径；失败日志保留原文件，返回首个具体错误与摘要即可。
- Sheet session `01a0e77c-a8be-755d-8bfa-4c3797bc3c09` 第105行，10:24:47：为查blocked状态打印除items之外整个status，意外带出所有physical_sessions，生成427KB原输出、51,376字符模型输入。给现有状态入口提供可直接选择的概况字段，比打印大对象后截尾更好；状态查询不需要把历史原生路径全部带入推理。

不能因出现安装或复验就判冗余。PR20的真实修正包括pivot删除守卫、菜单出视口与CSS括号；浏览器验收揭露了单测fixture未反映真实存储字段的问题。Issue5的undo修正有red-before/green-after证据。GH PR13还修正了种子与团队解析。完整成果与关键路径见[进展记录](continuation03-progress.md)；这些有效工作应保留。

## 决策排序与限制

1. **首先修一次性Context注入**：源码小、行为直接、证据强，既减少输入也避免反复把旧快照追加成新消息。风险集中在未接受prompt不得丢失初始数据。
2. **收敛休眠成员投递批次与原生复用**：不改责任模型，不禁止关闭后联系，不增加消息语义分类。需要核实通知收据、后台完成事件归属与Context更新失效边界。
3. **把长bash等待留给既有事件机制**：保留必要的提前查看与错误诊断，减少无变化轮询；先解决第2项造成的session更换顾虑。
4. **再优化有证据的重复核验与输出**：按候选变化和验证命题复用结果，保留发现真实缺陷的独立检查。资源争用与服务器消失另行取证，本页不把它们推定为CPU不足或Braid清理。

这里没有提出缩减必需验收、降低模型档次或删除工作记忆的建议。还不能把观察到的token减少换算为质量、完成时间或真实账单的确定收益；最佳下一步是修复第一项后在已授权的自然接续中看同session输入是否停止重复，并保留独立交付质量结果。
