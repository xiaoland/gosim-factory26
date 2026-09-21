# CLI 与配置收敛核验

本轮实现前基线为 Factory `9604e58`，Braid 起点为 `bd0cfcc`。用户明确不用实验验收；只做无模型测试、构建和只读历史证据核对，没有新模型请求、core probe、Playground 或 bench。

Factory 已改用 `variants/factory/config.json`，Pi/Codex 由 backend 覆盖；显式自定义配置标为 custom，历史 run 不经过新配置入口。旧六份配置及兼容链接删除，Git 历史与 run 自带 config 保留。list/show、outcome 与 feedback 单独记录 backend。Playground 只读取网关/模型配置，不能为 ZIP 切换核心；提交清单明确这一范围。

Factory 本地 68 项测试通过，覆盖默认配置、Codex 覆盖、自定义配置不回写、旧运行身份和 backend 过滤、失效入口提前拒绝。历史 `pi-svc` run 只读回放仍显示原 9/32；这不是本轮新分数。SVC status 为 healthy，导航与 Corpus 为 current；维护文档链接检查通过。

Braid 提交为 `e0c3ca2`。13 项单元测试和 1 项真实 CLI 集成测试通过，cargo fmt 与 cargo build 通过；新增迁移验证 v3 数据原样保留并升级到 v4。Clippy 退出 101，独立干净基线 bd0cfcc 也失败，主 Agent 对照两份日志确认错误多重集相同；不将它写为 lint 通过，也不在本轮扩大修复历史问题。

主 Agent 定向复核直接创建事务、writer fencing、request-id 重试和孤立分支处理，并补足空列表未知 JSON 字段拒绝与 view --comments。另在临时 Git/SQLite 状态中，通过真实 Braid 二进制运行 Factory 的 preparation_script（仅替换末尾的等待），验证 runtime/external/失效 writer 边界、comment JSON 和 status JSON；直接 pr create 重试不追加事件，hide/delete 正文不可见，PR description 读回一致。该检查没有启动 provider 或模型。

提交后已运行 sources.build('braid') 并通过 require_build：当前二进制、完整源码和 e0c3ca2 HEAD 的 build stamp 一致。修改后的 12 份入口/维护文档链接有效。Factory 与 Braid 分别提交，SVC 源码及安装未更改。

完整协作链仍未实施：父子 Issue、父 turn 让出执行位置、子结果唤醒、同类并行容量、共享材料版本和所有权继续在 design/plan 中讨论。单一 variant 不表示这些能力已存在。
