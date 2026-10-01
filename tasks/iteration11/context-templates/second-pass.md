# 第二轮：按需上下文

用户批准成员按需查询、PR仅展开OPEN关联Issue正文、讨论折叠、按模型窗口20%估算token分档，以及根协调时整理相关讨论。用户明确允许低档截短description；不启动实验。

## 接线与边界

`braid assignee list [--json]` 复用当前可指派目录查询，不创建新成员或改变指派语义。它对应GitHub repository assignees查询的用途，是Braid本地扩展，不伪称gh存在同名命令。CLI context前缀与共用instruction中的目录都已移除，instruction仅保留查询入口。

Profile新增context_window_tokens。I11 run.py从主模型models.json的contextWindow读取，避免单独维护两份窗口。旧配置使用128000的兼容假设，不能视为未知模型的精确窗口；已有配置可显式提供真实值。Issue/PR首次物化与接续、重建入口均调用render_budgeted；原字节硬限制继续存在。渲染预算针对工作项投影，固定角色指令和运行消息不计入该投影的20%。

scheduler日志记录tier、estimated_tokens、bytes；CLI context可用--window-tokens读取对应预算下的真实对象投影，不传则完整读取。CLI读取不改对象状态。

I11根定期检查的第二条消息要求整理相关Issue/PR：将已有决定归入当前说明、隐藏失效内容并说明理由、解决已结束讨论，保留未决问题。复用既有检查时机，无新巡检进程或自动语义清理。此前已有hide/resolve指引；本次补上协调中的使用时机，不能宣称仅有提示词就已证明行为改善。

## 当前核对

run.py语法编译通过。当前两份I11主模型配置（deepseek-v4-flash、glm-5.3-flash）均声明1000000-token窗口，实际注入预算因此为严格低于200000估算token；不会为显示降档而擅自缩小运行窗口。Rust编译与归档对象实际只读核对通过，渲染细节见 [second-pass-renderer.md](second-pass-renderer.md)。额外实际调用 assignee list 返回 deepseek/glm 名称与职责，help 与只读权限入口正常。源码实施完成。未运行测试、模型、实验，未提交或部署；I10仍暂停。
