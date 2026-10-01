# 本批实施与部署边界

2026-09-28，用户经协调会话批准：Closes生命周期、显式退订、工作记忆整理，以及进程归属/首次结果回执/有条件证据复用；保留此前token修复。
源码和指引已修改；用户随后明确确认部署这份清单。Linux发布材料正构建，当前冻结运行仍不变；未提交、未启动新实验。
SVC CLI/dev适用性评估见 [独立cell](cells/svc-cli-integration.md)：不默认接入、不新增工具，接线草稿已全部撤回。现有可选单服务helper保留。

## 问题 → 改动

|上游问题|实际改动与归属|运行影响与未证明的部分|
|---|---|---|
|PR写Closes却不关闭Issue，熟悉操作产生错误完成判断|Braid objects解析PR正文关闭声明；以origin symbolic HEAD识别默认分支；migration0014在merge intent保存目标；普通发布/已整合确认/恢复共同结算Issue状态。CLI view暴露closing_issues，create帮助和local文档写清边界|仅本仓库正文关键字；普通关联不关闭、非默认分支不关闭、失败不关闭。旧prepared意图默认空目标，不追溯推断。运行数据库会新增字段，不改旧声明或旧应用|
|退订后历史thread身份仍自动收件|discussion_changed排除明确inactive的历史参与者，仍保留负责人和当次@|只影响后续动作的收件决定；不删已排队输入|
|已有hide/resolve/edit能力未转为可执行整理方法|替换Braid共用指令原段，说明稳定依据、增量讨论、更正、窄改/hide理由、保留结论后resolve、受影响成员通知|LLM仍拥有语义决定；没有自动隐藏/分类器/评论数规则。实际采用和减少错误判断尚需后续运行|
|Pi重复把同一完整Context作为新输入追加|此前pi.rs修复，只有原生prompt接受后清除待注入context|拒绝和Deferred保留；旧历史重复不被追溯清除|
|终态成员积压联系逐条启动|此前store修复按当前身份/指派版本合批，逐条保留送达回执|不是跨休眠原生session复用；未实现该扩展|
|比赛成员全局pkill伤及其它检查|agent-browser现有技能中加入只结束持有job/PID/group的明确操作边界|不增加隔离或让Braid管理Pi内部进程；不强制用单服务helper迁移多服务run.sh|
|同tree缺退出码重跑17.2分钟；多层无差异全量检查|SVC verification两篇既有文档明确首次保留真实退出回执，按候选内容、检查代码、数据和运行环境复用证据；角色/merge commit变化不自动触发全量复跑|仍保留新风险/新覆盖的检查；不能用相同tree单独证明环境相同，也不宣称已节省运行时间|

耗时数据归属和with-service实际来源已复核：[来源记录](../braid-product-reaudit/cells/runtime-cost-provenance.md)。

## 验证

Braid定向行为检查共13项通过：Closes综合场景1项、退订真实comment路径1项、store closure8项、Pi协议3项。
Closes场景涵盖正文增删/多个目标/非默认分支/正常merge/已被Git整合/冲突/head不匹配/普通close/发布后恢复/恢复时正文被修改/旧意图空目标/重复恢复不重复关闭。
退订检查涵盖参与→退订→普通回复不投递→明确@仍投递→重新关注恢复，以及当前负责人按既有规则不能退订，仍承担本项通知。
日志保存于 `evidence/`；没有运行Factory或Corpus测试。指引只做源码审阅，真实采用尚未验证。

较宽的objects测试首次14项中8过6失败，不能报告整套通过。
失败涉及旧成员名预期、把SHA当head分支、旧副作用数量、英文conflict错误匹配、旧生命周期门禁、旧remove-assignee名称。
为区分本批新行为影响，在`/tmp/f26-braid-object-control`独立源码副本中禁用自动关闭和退订过滤、跳过对应新测试，其余12项仍有同样6项失败（另6项通过）。
这不是历史HEAD基线，也不是证明所有旧变更正确；只证明上述失败在不启用本批两项新行为时仍存在。
本批未改写这些旧断言来取得绿色，暂不扩展到其它历史行为修复；部署清单应明确这一验证限制。

## 已确认部署清单与边界

实际清单包括Braid源码/0014迁移、共用指令、agent-browser指引、SVC verification两篇文档；不含SVC CLI或新增工具。
用户已确认这份清单，无需再次授权。复用旧Linux runtime，只替换新独立发布目录中的Braid与已确认指引；当前冻结ZIP、活动会话和模型配方保持原样。新的发布材料记录于 runs/harness-releases/20260928-collaboration-v2，实际构建/包身份另记，不把材料就绪称为当前会话已经使用。
未来部署只影响新的输入与接续版本；已有会话中的重复上下文、旧送达队列和应用检查脚本不会自动被修订。
不能把源码测试通过等同比赛分数、实际采用或运行耗时已经改善。

## 后续新增范围（与上表部署分开）

用户明确多服务管理与首次回执问题仍须解决，不因SVC不匹配而停止。随后用户进一步澄清“可做小工具”不是具体方案确认：此支线停在设计复核，6-Sol只完成可评审方案，暂停源码实现与应用；已写草稿如实保留说明，不擅自撤销。新发布包不包含这条新增范围。
用户另外要求6-Sol深入诊断Sheet长时生成。两个派发请求因agent线程限额失败，现由同一个6-Sol优先处理只读Sheet调查，工具实现排在其后；主Agent继续发布包，不重复调查。
调查结果落入 `tasks/braid-product-reaudit/cells/sheet-progress-late03.md`；未获允许杀进程/改应用/强行结束。

## 11:58 UTC 新版发布材料完成

用户确认的范围已构建到 WSL 独立发布包：
`/home/yyh/Development/factory26/runs/harness-releases/20260928-collaboration-v2/pi-braid.zip`。
ZIP SHA256 `a04ca210e662650d7598c399f19f38870eccf7fc82f8718bcedc943192056ae8`；Linux Braid SHA256 `e2cde16dd9639ce570c465c650bc69ad1bbff230ce610320f6d5a30dee1fb3a6`。
构建复用现有 Rust/依赖缓存与 attempt-07 Linux runtime，没有重装 runner/npm/浏览器；只在新runtime目录替换Braid，原runtime没有修改。
实际读取最终ZIP，二进制及三份修改指引与manifest哈希一致；run.py、GLM/DeepSeek主profile仍与正在运行的03相同。
源码归档、构建命令/日志和release.json保存同一发布目录；本地同相对路径保存来源、release与选定材料清单。

**这是新的可用发布版本，不是当前Sheet会话热更新。** continuation-03保持原冻结二进制/指令/来源，未中断或重启；完成的GitHub应用与已评分重放也不改变。
因此不能把03后续采用、速度或评分归到本批修复。新工具方案尚未加入此ZIP。没有启动下一轮模型实验、没有官网新提交、没有源码提交。
