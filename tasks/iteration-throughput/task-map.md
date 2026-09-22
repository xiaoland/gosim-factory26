# 实施分工与集成状态

开工握手已批准，基线为 `7d3b1e6`。各 owner 在已有预演的接缝上实施；主 Agent 持有跨组件集成与实验放行权；获授权的运行 Agent 持有具体进程、等待和证据回传。源码更改的依赖按 [plan.md](plan.md) 验证，不将并行编码当作并行放行资格。

| Cell | 实施 owner / 写入边界 | 当前出口 |
| --- | --- | --- |
| Assignee | assignee_impl；Braid source/migrations/tests/docs，排除 provider/factory.rs 的 lifecycle 逻辑 | 配置/store/CLI/投影/恰一次 wake 的行为测试，`cells/assignee.md` |
| 能力装配 | capabilities_impl；profiles/native_profiles/factory/package、harness 配置与 submission Docker 构建 | effective 字段合同、同一 ZIP 材料和消费者测试，`cells/capabilities.md` |
| Competition | multiagent_boundary_advice；名字沿用旧会话，本次角色是实现者；competition.py 与测试 | 16 项 fake transport 检查、紧凑 summary 与只读恢复，`cells/runner.md` |
| Lifecycle / 集成 | 主 Agent；extension、Braid provider、core archive、submission 凭据、local runner、official matrix、联合资格脚本 | Node/真实无模型 Pi RPC、7 项 Rust provider 检查、归档与恢复行为验证，`cells/integration.md` |
| 环境 | 已完成独立只读取证 | Windows Docker 可用于打包；官方 local runner 基础 image 缺失；同一比赛 key 的模型接口已恢复，`cells/environment.md` |

CLI/对象的公开协作者字段固定为 `assignee_login`/`assignee_description`；variant defaults 使用公开 login，resolver 转为 Braid 内部 defaults（issue/pr profile ID）。文本与视觉 endpoint/key 分开，平台变量不能覆盖冻结模型。跨 owner 接缝通过这些具体合同协调，不复制各自实现。

原始 RPC、构建和运行日志留在 `runs/qualification/`；本页不累积逐条日志。只在接口假设失效、需要改变设计或外部事实需要用户输入时升级。默认输出阶段、状态、证据路径；完整日志按需读取。

当前并行出口：本轮边界修正已开工，Factory基线4310135。主Agent负责sources/braid，已提交fdb5c19（删除内部子代理控制，EOF关闭Pi），29单元与1CLI通过；factory_boundary_cleanup负责Factory源、被动观察/归档、删除全部自建沙箱及对应检查；direct_run_qualification优先负责短真实braid-scene，随后清理辅助入口和部署文档。真实运行先复用现有Linux runtime，不等新ZIP；一个候选官方闭环后再展开其余variant。此前进程兜底worker已中断。
