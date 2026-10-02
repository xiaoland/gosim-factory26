# G-ROOT-01：正文自更新重建会话，后台验收被丢失后重复启动

## 证据链（首轮原生 UTC08:04，进程/文件补证 UTC08:15）

1. root native `2026-09-29T07-24-07-088Z_01a0ec0c-a630-73db-a1a0-6351dbab5db3` record 24–28：在 `d62907d` 创建 `/tmp/verify-pr13` 并于07:27:57.947启动platform-path，PBB globalJobId=`pbb_44038_2d44e69d:bg001`，输出写 `/tmp/verify-pr13.log`。
2. 同session record 62/75：07:35仍install，07:38完成frontend build进入backend install。record65：07:36:51自行 `braid issue edit 1` 回写状态；record69收到自身正文变更notice；record78结束时表示等待bg001完成，且明确避免同时启动其它平台检查以免资源竞争。
3. DB `context_resets` reset `01a0ec18-51ce-77d1-b338-868bb71c23aa`：07:36:51 interrupting→07:40:17 applied，old session ec0c → new ec1b。唯一关联 `context_reset_events` 为本人writer_group发布的issue正文invalidate，非外部新需求或应用失败。
4. 新session `2026-09-29T07-40-16-998Z_01a0ec1b-72e5-70f7-a944-01b68deb0580` record15：看到pbb当前scope无job后断言“上一会话的验证未完成或未启动”，未消费旧globalJobId、日志或原PID；record17–18于07:43:06.805在另一个`/tmp/pr13-verify`目录重做同一`d62907d`的platform-path，再附加Vitest。
5. 新job record82完成元数据durationMs=906554（15分06.554秒），平台51/51完成。该job额外Vitest以工具Node v24运行而非应用Node20，75失败但管道 `npm test | tail` 的 `$?` 为0；模型在record70识别并修正，不能将其作为应用测试通过。
6. UTC08:15补证：旧PBB metadata仍status=running/outcome=running/exitCode=null，pid=45899，session进程44038；实际两个PID均不存在。`/tmp/verify-pr13.log`只到第12/51项，无最终退出标记，完整保存 `pr13-first-job-evidence.txt`。这证实旧作业未提供可消费终态，不证明任意时刻两份验收全程并行。
7. 实际部署原workspace的PBB源码已复制 `runtime-evidence/background-bash.ts`。`session_shutdown`调用abortAllJobs并清空待投递结果；process exit同样abort；任务scope默认当前Pi实例。该机制与原生/DB/进程证据相符。Braid为何在PBB未完成时关闭旧Pi需要继续对照恢复边界实现，不能仅凭当前源码认定具体行已触发。

## 根因与修复边界

这是三层衔接问题：自写正文触发重建；后台结果寿命绑定旧Pi实例；新实例只拿到“验证进行中”的正文，没有可恢复作业/结果引用，且把scope内不存在当作作业不存在。不能只要求模型更勤写packet：这里正是写packet触发重建。

最小修复先确定正文自写是否需要重建同一个负责人，以及已登记有限后台作业是否属于重建前必须消费的工作。若必须重建，明确终止/转交后台作业并保留终态与globalJobId；恢复提示提供对应读取入口。不要默认把长运行强制打断，也不要引入第二套同候选全量验收。

下一轮判别：同一候选启动platform任务后，负责人只更新状态正文，旧job最终结果仍能被消费；若确实取消，metadata与退出原因一致，新会话能说明重跑依据，不因`pbb list`当前scope为0就重跑。

影响边界：已确证至少一次同一候选从头重启及旧部分安装/构建/e2e进度损失。15分06秒为新一轮工作时长，不是可保证节省量；未将所有平台验收/墙钟等待判作浪费。

## 固定末尾增量核对

08:02:31 ec2f r25–26实际于08:08:20.888启动第三轮同d62907d（不是packet所写08:03），pbb_67630:bg001，直接在根持久工作区跑platform+Vitest。r31自改Issue1正文08:09:31，r34收到self body reset，r36 08:10:58平台到26/51，r37结束并期待后台唤醒。08:12:16 ec38新会话，r12 PBB current-instance0；r15只凭此断言上一任务中断并决定重跑，未查看先前job/log。r23–24在既存/tmp/verify-pr13解包，ls已存在node_modules、test-results；r28还猜git archive可能提交node_modules，没有核实目录清洁性。r29于08:15:57.946第四次启动同d62907d，pbb_73745:bg001。不能把这次称干净副本安装验证：脚本r22明示要求调用者提供clean copy，且root node_modules存在时跳过install。

第四轮r47 08:20:37返回vitest exit0，r50记录platform51PASS+platform exit0、Vitest95PASS+vitest exit0。r61–63实际合并PR13，08:24:43回包merge=e9390cc5a7ad309760402db83d9c97e293abc420；r65 fetch确认develop同hash。此为原生合并动作与Git读取双证，不只评论。此前第三轮终态未取到，不能把4次启动说4次完整重复运行或量化全程浪费。

末尾还有基线前移成本：08:16预演#13合并后#15需解冲突，5个冲突marker一度错误写成5个文件并列7路径；主Agent继续核实，截点r65确认#15 marker5/#16 marker2，不直接作为精确冲突文件结论。M5刚因docs-only补跑平台后又需消费M2实际代码变更；后者重验有实际理由，应与纯文档重跑区分。

## Braid→Pi→PBB生命周期代码补证

固定5c957436源码已保存runtime-evidence/。worker.rs 337–345在reset notice被处理且turn completed时先sessions.remove，再记reset终态；session_manager.rs 142–164先factory.teardown，PiSessions factory.rs 316–322调用close_native；provider/pi.rs 76–103丢弃stdin writer，用EOF调用Pi原生dispose/extension shutdown（等待最多180秒，超时kill并返回失败）。部署PBB 971–975的session_shutdown则abortAllJobs，905–915中abortcontroller并SIGTERM进程组、clear active/pending。说明reset会结束原生作业所有者，并非仅重写prompt。PBB agent_end对!hasUI的finite jobs另有等待，不能忽略这个反例或假定所有turn结束必杀作业；实际观察到的reset替换、旧pid消失与未终结receipt应共同使用。当前只核实代码生命周期，不改变源码/启动验证。

固定5c957436 provider/pi.rs 567–625已核对：Braid以agent_settled关闭物理turn，而不是assistant message_end；后者只记录stopReason。故不能建议把message_end换成settled作为本版修复。ec38 r42–43在bg001运行时subagent_wait仍回“No active async runs or registered provider work”，原生后台登记/等待边界需要另行判别；此处未证明hasUI值或登记失败具体原因，不补造。
