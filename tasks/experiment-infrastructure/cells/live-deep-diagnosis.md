# DeepSeek attempt-06 运行语义与设施诊断

只读取证，观察截至 2026-09-28 05:10 UTC。现场是 WSL `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/` 下 GitHub、Sheet 两条仍运行的恢复任务；原 Braid run ID 分别为 `20260928-030347-78b10c07`、`20260928-025746-66feadac`。以下“新窗口”从约 04:49 UTC 的 attempt-06 真实恢复算起；此前的 source-native、旧 Pi 消息与尝试的故障不能充作本次模型行为。没有改源码、运行输入或停止任务，也没有做 Factory 测试。

## 决策用发现

1. **恢复后已有可消费产出，GitHub 的交接失败由成员自行纠正。** GitHub `glm-2` 在两次“delivered”后仍未提交、推送或提 PR；根成员 05:04:04 的原生消息据 origin 与工作区作出这个判断，接管其工作区内容，验证前后端后于 05:06:31 报告 PR #1 合入 `develop`（`012fb04`），随后 05:07 分派 #3/#4/#5，DeepSeek 成员开始出现原生请求。故问题是“自然语言交付声明未对应 Git 制品”的成员执行/核验缺口，不能写成 Braid 投递失败，也不需立即中断运行。Sheet 在同一恢复窗把公式引擎 PR #1、共享基础 PR #2 合入 `develop`（`87cedb5`），解除 #3–#7 的依赖门控；这些是 Git/PR 事实，仍非最终应用验收或评分。证据：两份 `braid-state/braid.sqlite3` 的 `work_items`、`local_comments`；GitHub comment #5/#7–#10；Sheet comment #39/#41–#50；原生 Pi JSONL。最小工作方法是成员报告“已交付”时附 commit、远端分支、PR，根成员以 origin 实测后再放行依赖。

2. **Sheet 的合并门槛先于真实浏览器交互，后续检查找到了实现缺陷。** 共享基础 PR #2 合并前证据是 build、种子、REST 与 GET / 200；`glm-4` 随后实际跑浏览器检查，发现 Grid 单击后 Shift+click 未扩成矩形，区域 `aria-selected` 不正确，并于 05:07:42 提跟进 PR #3（`23e1dd1`），同时修正检查脚本本身的问题。这是有具体用户行为的回归，不是单靠测试数量或对当前 DOM 改断言的“通过”。建议在最终默认入口核对这条交互及需求原始判据，待 PR #3 合入后再判 REQ-1 网格完成；此时 PR #3 尚 OPEN。证据：Sheet Issue #2 comment #51，PR #2/#3 状态及对应原生工具记录。其它功能仍在各自分支，不能把 #3–#7 的准备件或评论写成已交付。

3. **OTLP 新窗的 `Timeout(5s)` 是 evidence flush 等待超时，缺失量目前不能计算。** GitHub 在 04:52:20、04:59:20、05:04:10、05:06:09 发生 4 次，Sheet 在 04:59:15、05:00:10、05:03:42、05:04:00、05:04:11 发生 5 次；均为 `braid-state/telemetry-errors.jsonl` 的 `capture_error: Operation failed: errs: [Err(Timeout(5s))]`。Braid `EvidenceWorker` 每 5 秒 `capture`，`EvidenceWriter` 每 64 条及结尾调用 `SdkLoggerProvider.force_flush()`（`sources/braid/src/telemetry.rs:283-305,402-430`）；当前 WSL 的 opentelemetry_sdk 0.32.1 `BatchLogProcessor::force_flush` 固定 `recv_timeout(5s)`，provider 把它包装成该错误。现有错误没有标出是第几个 64 条 flush 或末尾 flush。两题新窗 `receive_errors` 都为 0，之后 logs/traces/metrics 持续到达；这证明接线可用，不能证明超时批次已完整重发。worker 出错会重建 `EvidenceCollector` 并在后轮重送，但已入队、已落盘、SDK worker 超时后是否最终提交的边界没有逐记录收据。出错后的运行/代码继续推进，未见它直接阻断模型。

4. **采集负载与页面输出偏重，设施易把“有大量证据”误读成“证据完整”。** 04:49–约 05:10 UTC，Sheet 收 logs 227 批、131.3 MB，GitHub 133 批、28.6 MB；Sheet 出错附近 04:59、05:00、05:04 每分钟分别收 17.9、18.9、20.8 MB。新窗原生 JSONL 当前约 9.0 MB/2.2 MB，而 `EvidenceCollector::capture` 每 5 秒重新读取整份原生会话并对增长版本生成新 artifact，故采集量大于源文件并非模型成果量。一次已有 viewer 入口生成的静态快照，Sheet `decoded.json` 443 MB、`index.html` 28 MB，GitHub 分别 79 MB、4.8 MB；页面生成时 715/345 批且标 `partial`，它不是持续更新的实时终态。viewer `analysis.json.source_capture_errors` 是有界索引条目数（Sheet 50、GitHub 40，混有 Braid WARN/ERROR），不是这次 capture 超时次数；原始文件在 `source-errors/` 才能按时间窗计数。建议先让 capture/flush 记录阶段、耗时、待提交条数和本轮发送记录数，并在分析页显示源端超时与接收端批次的不同含义；只调整 HTTP timeout 不能解决 SDK 固定 5 秒 flush 等待。减慢全量抓取周期可能降负载，但须在真实运行测量后决定，保留终态抓取。

5. **历史缺口与本次运行状态须分屏解释。** Viewer 对 GitHub/Sheet 分别重建 4/15 个 Braid session，但 `reconstruction.json.gaps` 同时列出旧恢复阶段 native 路径不可读、Sheet 三个旧 DeepSeek session header 不匹配、`final snapshot is missing` 和未归档子会话清单未知。旧路径属于 04:49 前的材料，不证明 attempt-06 新会话丢失；`final snapshot is missing` 在仍运行时也属预期。相反，`partial` 不能抹掉第 3 点的新 capture 超时。当前基础计数应分别从 Braid DB、原生 Pi、OTLP 接收表读，不把 18 个原生/历史会话说成 18 个当前成员。两题本轮 `wake_batches` 新建批次 `event_count` 均非 0，未观察到空唤醒；GitHub 直到 05:07 才有 DeepSeek 参与，因此历史“DeepSeek GitHub 尚无 DS”结论已过期。

6. **运行限额可能放大采集与工具尾延迟，未见 OOM。** 两容器 `docker inspect` 均为 2 GiB/1 CPU。约 05:16 UTC 的 `docker stats` 工作集为 GitHub 1.142 GiB、Sheet 1.486 GiB；随后 `memory.current` 两者都接近 2 GiB，Sheet `memory.events max=130999`、10 秒再增 800，`oom=oom_kill=0`。Sheet `memory.pressure full avg10=14.14%`，GitHub 2.67%；`cpu.stat` 累计被限速时段 Sheet 9826/17182、GitHub 4225/17041。说明 Sheet 多 Pi 与采集在受限容器中有真实内存回收/CPU 争用，可能放大 5 秒 flush 超时与工具检查耗时；无法仅凭同时出现证明每次 timeout 的单一原因。主线下一次真实验证宜同时保存这些 cgroup 指标与 flush elapsed，不在本次只读任务调整资源。

## 复核入口与边界

- 当前生产者：两例 `workspace/official-generation/template/.factory26/<run-id>/` 下的 `braid-state/braid.sqlite3`、`sessions.json`、`telemetry-errors.jsonl`、`pi-timing.jsonl`、`work/native-homes/*/*.jsonl`，以及同目录自包含 `telemetry.sqlite`。只用时间 `>= 2026-09-28 04:49 UTC` 统计新窗错误及接收吞吐；旧记录未删除。
- 已执行包内现有 `lab.analysis.braid_telemetry_viewer`，只读原始 OTLP，输出为 `attempt-06/generation/analysis/live-deep-github-0505/` 与 `live-deep-sheet-0505/`，`analysis.json` 记录 batch 截点、工具与 Braid 哈希；原始诊断文件保存在各自 `source-errors/`。未以页面截图或“receive_errors=0”判交付质量与完整性。
- 由于恢复会话仍增长，以上 Git/PR 状态、模型活动与批次数是观察时截面。没有最终交付、外部评分或供应商账单证据；也没有足以量化 OTLP 丢失记录数的 source→flush→collector 逐条确认链。Qwen/MiniMax 只作旧 attempt-02 未完成对照，不能据其旧 token、成功请求数与 DeepSeek 新恢复窗比较完成速度。
