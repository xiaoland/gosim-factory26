# 实施计划

用户已批准 design.md 并明确开工与自主提交。本计划收敛已批准范围，不重新申请同一授权。

先修三个底层责任面：process_state/process_identity 统一 controller/worker 三态；Controller.launch 和 monitor 动态 targets/accepted/exit；恢复来源/目标解耦及 recovery.prepare。三者可以独立实施，root 集成 API：恢复返回冻结 package 与具体 receipt，launch 返回实际 journal summary，monitor 提供 accepted/first_batch，identity 提供非空出生依据。

主线并行实现输出保全和一次自动回收，再实现 lab.arc_bench operation。规格沿用 local recipe 与 hosted prepare 字段，prepare 固定实际内容，run 复用原操作目录、既有外部身份及 scheduler，status 只合成权威观察。后台 worker 持久记录身份/错误/终态，local replay 跟随接收与 observer 接收独立。

独立预演针对实际接口和失败接续进行，只分析调用与真实原件，不构造测试。集成后以 Python 编译、真实旧进程记录、保全输出归档、独占无网络恢复准备及既有终态 journal 观察取得反馈。所有记录保留 source/attempt 身份和原始错误，长操作由程序写完成回执。

现行四项运行、collector、Console 不参与首轮改动应用。首轮不启动模型或官网收费运行；这些行为的实际验收须在既有明确实验范围内确认具体接入，不能用无模型准备替代 provider/评分结论。已有未提交 competition/package_arc_replay 等差异保存为baseline，最终仅提交本任务及其必要锁范围前提，其他任务差异保持在工作区。

已完成上述实施和本轮无模型实际反馈。用户新增架构要求已应用到统一attempt范围、恢复证据冻结、公共观察回执和单一自动回收责任。完整结果及未验边界见packet与implementation说明；新增模型执行和I14逐项条件撤销均不自动进入本轮。
