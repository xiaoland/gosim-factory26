# Console 历史部署与暂停机制

本页保留旧冻结服务的时点事实和机制，用于解释已有证据。当前服务准备、登记与控制边界见 [Console 手册](../console.md)。这里的 PID、目录、登记项和旧 pause 方法不表示现在仍在运行，也不授予恢复或清理权限。

## 旧服务的独立访问与暂停门闩

旧冻结服务通过单独的 CLI 访问容器共享生成现场。访问容器使用原镜像、用户、工作目录与挂载，以 sleep 待命并隔离网络；Console 在该容器中执行对象 CLI。旧配置固定生成容器、访问容器、Unix socket context、binary/state/mounts 与 service/run 标签，但未采用新 attempt 域的 `access_resource_id`。旧手工创建过程不满足当前登记合同，不移植为新服务步骤。

当时页面 pause 冻结生成容器的 Agent、子进程和 Braid 定期检查；独立访问容器继续读取与人工输入。适配层在同一 Linux 访问容器的现存 WAL 数据库执行 `BEGIN IMMEDIATE`，取得写者锁后暂停生成容器，确认 Paused，再 `ROLLBACK` 释放；它不修改 Braid 数据行。已经暂停的现场再次 pause 只核对并释放写者锁。此门闩需要访问镜像具备 Python3/sqlite3 及可写共享数据库挂载，不能由另一内核的宿主连接替代。

直接 Docker pause 若冻住现存写事务，门闩可能失败。历史处置保留具体 SQLite 错误、Paused 状态和 journal，不清理锁文件、复制 state 或自动 unpause。写锁可取得、对象读取正常、业务修改完成和恢复检查点完整分别核实；物理暂停不是完整恢复检查点。

旧验收曾读取各 run 的列表、根 Issue 与 PR，核对原容器 Paused，并在已有暂停状态下验证 `BEGIN IMMEDIATE→ROLLBACK`。这些回执解释当时冻结实现，不能用来验收当前拒绝 pause 的程序。原接线及故障证据见 [暂停访问记录](../../../tasks/iteration13/console-paused-access.md)。

## I12 与 I13-2 的部署记录

I12 已在独立磁盘清理中终止，归档位于 `runs/wsl-retained-20260930/`；不以恢复其暂停现场为目标。旧 I11 摘剪接续也已停止。运行身份、部署 PID、人工输入 journal 和停止证据见 [I12 packet](../../../tasks/iteration12/packet.md)、[Console 记录](../../../tasks/iteration12/console.md)与[部署记录](../../../tasks/iteration12/deployment.md)。

2026-10-01 的 I13-2 首次切换直接部署在 Debian-Rebuild，稳定根为 `/home/yyh/.local/share/factory26/exp-console/20261001-i13-2-compatibility-release`，service ID 为 `8cc80cad-d873-49ed-ab49-e958ba8852a3`，记录的 HTTP PID 为 776190。Mac 的 8765 使用独立 SSH 转发；HTTP 与转发当时均未配置自动重启。旧 HTTP PID 163346 已退出，旧自有访问容器已停止、manifest 已退役；配置与 journal 保存到新根 history 并校验。

当时登记四项：`glm-root--hackathon--github-f9e238c1b698a5` 与 `glm-root--hackathon--sheet-a45a22ec644204` 为只读 archive；r2 的 `glm-root--hackathon--github-a94a67b4b3d85b` 与 `glm-root--hackathon--sheet-8046cfb0695023` 为 live，绑定各自新卷及原 Braid namespace。首次失败尝试未登记到新卷。实际 HTTP/UI 覆盖四项 Issue、PR、sessions、两项 runtime，以及隐藏祖先下后代默认省略和单条展开；没有业务写入或生成控制。准确制品与边界见 [I13-2 部署记录](../../../tasks/iteration13/i13-2/console-deployment.md)。

当时访问容器沿用原 named volume 与同一 `volume-subpath`，保留消费者引用。记录中的清理顺序是关闭转发和 HTTP、停止访问容器、release 接入、明确移除该容器，再处理实验资源；它属于旧控制合同。仅停止访问容器仍占用 volume，原生成 runtime 移除后保留材料读取不代表仍可控制生成。

2026-10-02 的审阅阅读修复切换到 Debian-Rebuild 的 `/home/yyh/.local/share/factory26/exp-console/20261002-review-sessions`，保持上述 service ID、七条登记及原 binary/访问容器绑定。记录的 HTTP PID 为 1676167，instance 为 `8ccaaf92-02f0-4a60-904e-5564ba6957c3`。旧 HTTP 已退出、旧 manifest 已退役，原配置及 journal 保存到后继根 history；没有新增访问容器、模型运行或自动启动，Mac 转发沿用原入口。

该轮实际操作覆盖 PR2 → review1 → reviewer agent → provider → 原生对话/Trace、provider 深链刷新及返回审阅；七项 Issue/sessions 与真实 reviewer 正文均返回 200。部署与具体边界见 [审阅阅读记录](../../../tasks/console-reviewer/packet.md)。以上远端路径属于历史执行存储，不是 Mac 的部署建议。

## 已取得反馈与证据入口

历史已取得真实 Pi 原文接口与页面反馈，以及归档深链和前后导航反馈；不能据此宣称 Codex 正文、可写现场草稿保护或生成控制也已实测。前序与后继证据按各自实际制品区分：

| 证据 | 记录 |
| --- | --- |
| 会话目录、身份和关系 | [会话导航](../../../tasks/braid-console-control/session-navigation.md)。 |
| Pi 对话、Trace、工作区与 origin | [会话阅读](../../../tasks/braid-console-control/provider-session-reading.md)。 |
| 路径路由、归档导航与 UI | [路由回执](../../../tasks/braid-console-control/path-routing.md)。 |
| 控制设施范围与授权 | [独立 Console 任务](../../../tasks/braid-console-control/packet.md)。 |

旧冻结实现继续按原身份取证；当前新程序尚无 Harness 公共静止协调合同，拒绝 Console pause。是否已有新制品部署，须从实际服务 manifest、active 回执和对应部署记录确认，不能从工作树代码改变推断已迁移。
