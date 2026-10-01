# 热恢复期间的可观测性与检查工具

2026-09-28 用户明确授权快速热观察、定位后修复并保留半成品接续。

## 原生材料选择错误

在 attempt-06 GitHub 用新的 `native_profile --since 2026-09-28T04:49:39Z` 查询时，出现 156 个新模型请求、零条对应 assistant 用量、零会话且 gaps 为空。
实际 `native/manifest.json` 是 attempt-05 恢复来源留下的 partial 归档，只有四个旧 session；真实新会话在 `work/native-homes`。
旧实现只要 manifest 存在就不用 live 材料，因而把新时间事件与旧 token 材料混合，却没有指出覆盖缺口。

修正在两处现有边界：恢复入口在启动 Braid 前归档来源 native，避免整段恢复期间把旧归档暴露为当前记录；分析入口对非 complete 的 manifest 合入实际 live sessions，仍优先使用终态 complete 归档。
实际重读同一运行后，恢复窗已有 GLM 126 条、DeepSeek 34 条 assistant 消息及输入/输出/cache 数据，gaps 为空。
这是动态截面，不与第一次相隔的请求数直接相减衡量缺失；只证明原先漏掉的新消息现在进入查询。

## 时间窗与身份

`native_profile.py --since <带时区 ISO 时间>` 支持只观察某次恢复后活动。
用量按 assistant 响应时间计，耗时按操作开始时间计；跨窗口请求/工具排除数量单列，不把跨边界累计耗时伪装成窗口耗时。
模型表区分逻辑 Braid 成员（group + assignment generation）、原生主会话和 Pi 子会话；没有足够身份字段时成员数显示未知。
主会话数不再仅依赖 timing 中出现请求，还统计已有用量消息的会话。
运行中的未结束请求用量仍未知；字段为零不等于供应商免计费。

真实证据：WSL /tmp/factory26-gh-profile-window-v2.json；读取使用 /tmp 独立分析脚本，不改冻结 code。

## Skill 内通用服务检查工具

现有 `agent-browser/scripts/with-service.py` 接受 cwd、前台服务命令、端口、就绪路径和调用方的检查命令。
它预先拒绝被占用端口，传递 PORT/BASE_URL，等待本地 HTTP 成功，监测服务存活，保留服务日志/检查日志/退出回执，并清理自己启动的进程组。
它不选择业务判据，不编写应用文件，不隐式创建或重置应用测试数据；服务本身按其代码初始化的行为不由工具代替判断。
不添加独立技能，不强制更换浏览器，也不实现第二套后台任务系统；PBB 可执行整个命令。

实际使用 Sheet 已生成后端 dist 的临时副本，连接其既有依赖，运行 `node dist/server.js` 并 GET `/api/workbooks`，端口18437。
结果服务 HTTP200、检查 exit0，收到初始工作簿响应；结束后端口不再监听。
日志与回执：WSL /tmp/service-check-rni7n_za；应用副本 /tmp/factory26-sheet-service-ca0l910w。
原工作树及其数据未修改。
这是实际生成应用操作验证，不是 Factory 测试或模拟探针，也不证明应用满足全部需求。

运行深析与 capture timeout 根因由 live_deep_diagnosis 并行调查；vision 专项见 ../../braid-product-reaudit/cells/vision-root-cause.md。

## 证据采样负载

运行深析已将 capture_error Timeout(5s) 定位到 SDK BatchLogProcessor 的 force_flush 回执等待，不是已证实 HTTP 请求超时。
当前 Sheet 二十分钟量级接收约131.3MB日志、原生源文件约9MB；变更版本与失败后的全量重发放大流量。
先把证据快照周期从5秒改30秒，结束信号仍立即补采；普通 traces/logs 不受这项周期影响。
保留64条flush阈值，避免同时增加四倍小批请求而混淆因果。
flush错误新增pending记录数与耗时，capture错误新增总耗时和是否终态，以便下一热运行辨别压力与缺失。
此修正是减负并取得区分证据，尚未声称消除超时或证明完整率。

2026-09-28 attempt-07 实际证据：Sheet 在4GiB/2CPU、30秒采样下仍出现一次 flush 13条pending/5000ms超时（05:37:33 UTC）；至05:43截面接收继续，未出现新一条。不能据此把根因确定为单批64条或资源额度。当前保留原始诊断，后续先区分接收/持久化耗时和SDK等待，不继续试调阈值。
