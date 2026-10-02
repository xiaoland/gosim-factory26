# GitHub 全过程审查

2026-09-29 开始。授权来源：协调任务明确要求从头全面审查；只读运行材料，仅在本目录写调查产物，不改源码、应用与运行状态，不执行测试。

## 身份与截点

运行 e20260928-03-check-receipts，原 workspace 的 inner 为 20260929-042409-1202e245。恢复链为 generation → hotfix-01/generation-02 → hotfix-02/generation。旧 cancelled controller 不能代表当前运行失败。
首轮采集窗口 UTC 2026-09-29 08:04:30.462358 至 08:04:36.517118（北京时间 16:04:30–16:04:36）。原生文件逐文件读取，数据库以只读源连接 backup 到内存后序列化；这是调查截点，不是可恢复运行检查点。源路径、文件哈希和长度见 snapshot-01/manifest.json。

## 计划与恢复入口

1. 已完成首轮原始材料保存、对象索引。唯一覆盖账本为 coverage.json；文件已索引不等于已读。首轮命令的目录清单显示截断，现以完整 manifest 补齐索引，不能计作过程阅读。
2. 分段读根统筹与共享基础、M1/M2、M3、M4/M5 和子 Agent，逐条保存阅读范围、原文定位、竞争解释与缺证。局部 cell 的阅读凭据最终合入唯一账本。
3. 跨链核对 Issue/PR/评论、真实 Git 动作与恢复时序；响应去重后汇总成本。usage.json / cost-summary.json 已按3507个唯一responseId复核；reasoning属于output子集，不重复计数。
4. 形成 report.md，核对已读/缺失/截断补读；另采一次有界增量并明确首轮结论有效范围。完成或阻塞通知协调任务。

本目录独占。其余 Agent 的代码和任务文件不属本审查写入范围。

## 最终状态

固定材料审查完成。首轮121个native来源归并为111个canonical单元、9,035记录；16份Issue/PR board、99份唯一turn input（1021来源）及运行身份/材料/四份Braid日志完成对应审查。唯一末尾增量12个native文件新增824记录、14份turn输入、评论134–149与生命周期日志亦完成。主账本 `coverage.json` 的111单元均为complete-readable-content，无未读实质单元。

阅读口径为实际消费全部可读正文、thinking、工具参数/回包、details、custom实质内容；精确重复引用首次已读来源。早期record顺序/程序遍历/投影统计冒充全文的声明均已撤回并补读。根链最终依据Sol前15单元回执、Luna后段真实1600000字符回执、主侧脚本与流一致性核实/26个argsPayload补读，以及Sol最后U23 r84–85/U24补读；不依赖旧完整声明。message字段另做schema核对，首轮4条及增量1条errorMessage完整记录均已补读。

边界：图片像素未重新视觉验收；两段woff2字体base64不解码；包装metadata与遥测结构事件按结构核对，不声称每个事件逐字阅读。原生grep/tail/模型长度截断不能恢复。snapshot-02中ec45创建日志已到而native文件未采到，保留非原子采集缺口，不继续抓取。成本固定首轮3507唯一responseId的已记录usage；两个terminated响应留下partial内容但usage为0，因此不能把表格当实际账单。

结论和优先范围见 `report.md`：后台工作与Braid turn寿命分离、reset长turn延迟评论、原始检查错误被过滤后结论增强、docs-only回写触发重复验收。PR11/14后台完成后的写入拒绝最终经新wake/notice恢复；PR13末尾合并至e9390cc已由回包与fetch确认。SQLite锁与旧结果写权限由iteration10紧急修复负责，本审查不重复立项。

已完成报告与覆盖一致性核对，并通过send_message_to_thread一次性成功交付协调任务01a0bcc1-62fe-79b1-87d4-5d8a9d1199ed；工具返回成功，无需重复发送。未修改Harness/应用/运行状态，未运行测试/实验或提交；源码实施与新增实验仍不在本授权范围。
