# 新实验：重置通知重复延后被记为失败

2026-09-29用户要求“排查”。用户随后明确授权：“后续你遇到这种信号明确的缺陷，应该立即热修复，不需要和我核对”。本缺陷进入修复及热部署阶段；保留半成品及运行身份，不因投递繁忙强杀仍在工作的原生会话。

## 已确认的现象

GitHub run `pi-braid--hackathon--github-7fe42a1248f9d8`、PR #2旧会话出现819条`trigger_kind=context_reset_notice,lifecycle=failed`的记录。
这些记录均无started_at/error，ended_at范围为04:46:42.862至04:56:23.996Z。
同一reset于04:56:24进入一次真正running的notice投递；原生会话04:56:24.418Z确实收到“当前会话结束后会用最新内容重新打开”的通知。
此前原生会话一直在执行agent-browser、开发进程收尾和平台安装/验收脚本，04:54至04:56仍有正常assistant与工具行为。
不能将819次重试等同819次模型调用失败或十分钟没有业务进展。

## 因果链

1. `store::claim_context_reset_notice`依据持久化provider_sessions.idle领取reset；每次INSERT新的starting turn。
2. `dispatch::start_next_agent_turn`使用非steering的send_user_msg。原生/适配会话暂不能接受时返回Deferred。
3. 此路径调用defer_context_reset_notice(retry)：turn改failed，只有ended_at，不记录Deferred原因；provider_sessions恢复idle，reset.active_turn_id置空。
4. 这恰好恢复了下一轮领取的全部条件，因此驱动循环继续领同一reset并创建新turn。
5. monitor只计started_at>=本次开始的failed记录，所有未开始的投递重试均被过滤，摘要仍显示零。

`provider/session.rs::send_user_msg`在内存Running与非steering不匹配时返回Deferred；`provider/pi.rs::start_turn`也会在原生streaming/compacting时返回Deferred。
本轮未保存具体Deferred文本，不能确定819条分别经过哪个guard。
Pi的后台follow-up可在已settled之后继续原生工作；Pi reader在没有受管turn_id时将这些活动作为idle activity忽略。它与Braid持久化idle不是同一个“空闲”定义，是需要核对并修正的生命周期边界，不能凭表中idle推断原生可接收新prompt。

## 已授权修复方向

- 保留“旧会话先获知更新，再完成交接”的产品行为；原生继续工作是合法状态，不为清理数据库记录强制终止。
- 重置通知作为待投递输入保留；Deferred不代表一次已执行turn失败。不要每轮重新创建失败turn，用真实接收事实建立执行记录。
- 原生Adapter应表达真实输入可接收状态/恢复可投递的变化，包含后台follow-up活动；调度按该事实再投递，避免由数据库idle反复发起。正常输入与重置通知应共用此边界，不能另做只针对reset的睡眠补丁。
- 对延后原因保留原始文本、首次/最近时间和次数，诊断摘要将未开始投递与已开始执行失败分开。
- 监控增加明确的未开始投递事实及当前reset阶段/持续时间；用时间字段实际含义限定本次尝试，不把所有无started_at的旧记录算成新故障。

## 证据入口

远端实验根：`/home/yyh/Development/factory26/runs/e20260928-03-check-receipts`。
数据库：GitHub run的`workspace/official-generation/template/.factory26/20260929-042409-1202e245/braid-state/braid.sqlite3`。
原生JSONL：同内层目录`work/native-homes/pi-deepseek-fast-01a0eb6f-2435-7b40-8c0d-ca9ef86d9bfc/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.jsonl`。
源码：`sources/braid/src/store/mod.rs`中的claim/defer_context_reset_notice、`group/dispatch.rs`、`provider/session.rs`、`provider/pi.rs`；监控`tasks/iteration10/scripts/monitor-generation.py`。

## 热部署进展

用户明确要求立即修复，不再逐次确认。2026-09-29 05:09:47 UTC 已暂停两题容器，保留原工作区；热部署目录为 WSL `runs/e20260928-03-check-receipts/hotfix-01`。两份 SQLite 已用 backup API 保存。Braid `640ebd8` 完成编译，正在构建 Linux 二进制；使用既有 continuation 接线恢复同一 Braid run，不重建应用。监控同时补齐未开始投递失败和 schema 16 的待投递记录。

2026-09-29 05:21 UTC 热部署成功，Linux binary SHA256 `f974830709a62d5583a194997076c1b634e4e3a96f60df0876070f34e9db202f`。首次接续因容器 root 与原工作区 UID 1000 不同遭 Git 归属检查拒绝，尚未进入原生执行；修正 continuation 按原工作区 uid/gid 启动后，在 `hotfix-01/generation-02` 接续。GitHub `pi-braid--hackathon--github-575299dc237d16`、Sheet `pi-braid--hackathon--sheet-2faf63f9812725` 均 running，schema 16 字段已迁移，初查分别4/2活动turn，恢复后失败数0。Sheet有一条invalid Pi session警告，交原修复worker追查，未据此声明所有原生会话恢复完成。监控使用更新脚本，3分钟/8分钟采集。

Sheet 恢复警告已核实：旧 PR #2 JSONL 缺 session 头；此前待处理的 context reset 于05:21:48完成，新 provider session 已建立，根 Issue 于05:21:51也完成替换。警告对应已淘汰旧会话，不是当前恢复阻塞。缺头产生原因尚未确认，不能归因于本次修复；保留作后续会话归档定向调查。
