# 工作方法与工具使用

状态：本轮方法材料已修改并完成静态核对；未启动 benchmark，未改冻结运行或应用内容。

## 落点

- SVC Verification 定义“需求→观察与判据”、场景前提和结果归因；Task Packet/Design/Implementation 在需求交接与共享契约发布处接线，不重复定义验收方法。
- `browser-checks` 说明真实用户入口、合法 setup、候选服务的 cwd/env/日志/真实退出码。执行角色按现有 PBB 完成通知与 `pbb status/tail` 消费后台结果，不新增服务框架。
- 两个活动 variant 的原生成员指令只提供使用上述方法的短入口和协作交接时机，不加入题目选择器或业务断言。

## 核对与验收

已核对 `runs/e20260927-01-handoff/stage/runtime/node_modules/pi-background-bash/README.md`：1.0.5 支持 `background: true`、30 秒自动转后台、完成消息唤醒、每 job 的 PID/PGID 与完整日志，以及 `pbb status/tail`。两个 variant 的 `run.py` 均将扩展装入成员和有 Bash 权限的原生角色，创建 `pbb` 命令，并复制 SVC/browser-checks 材料。PBB 只能报告所调用 shell 的退出码；`tail`/`echo` 掩盖的上游状态须由命令自身保留。Pi-lane 的会话存活不能证明应用服务归属。

已检查方法材料与五份原生成员指令的落点：SVC 定义通用原则，browser-checks 写工具操作，角色提示词只把方法带进拆分、契约交接和失败判断。依据仓库规定，不为 SVC Corpus 或开发设施增设内容测试；方法效果留待已授权真实任务观察。

2026-09-28 最小修订：用户允许明确禁止实现反向决定判据。仅替换 check-design 中现有修订 oracle 的句子，明确判据变更依据必须是需求或被纠正的需求解释，不向各角色重复注入。
