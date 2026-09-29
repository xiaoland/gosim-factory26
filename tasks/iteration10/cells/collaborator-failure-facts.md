# 协作者查询最近执行事实

用户已授权继续修正；collaborator_failure_facts负责Braid实现及本cell，主线整合。
方案及边界见 ../repair-review/final/product-runtime.md 第1节。
实施状态：已在 Braid 沿既有 `turns` / `provider_sessions` / `assignments` 保存与查询事实。迁移 0015 给 turn 增加原错字段，给恢复错误增加发生时间；worker 和 dispatch 的终态路径将 provider 或派发原错与终态同事务保存。当前 assignment 的最近终态、会话恢复、被阻断的指派或 reset 参与 Issue/PR 查询；成功终态、成功恢复和新指派不再投影旧故障。

Agent `status --json` 的每项新增 `execution`：当前故障时含 `outcome`（`failed`、`unknown`、`recovery_unavailable`）、`at`、`summary`，否则为 null。Issue/PR view 同样显示；`--json execution_error` 读取去除 UUID 的完整错误，原文仍在数据库。事实只说明最近尝试，不表明业务完成，不触发改派或广播。

依用户暂停边界未做测试、模拟探针或实验；`cargo check` 通过，原有 dead-code warning 仍在。SQL 查询未做动态验证，需在主线整体交付时按用户恢复实验决定验证。未提交。
