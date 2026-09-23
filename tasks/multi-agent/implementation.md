# CLI 与配置收敛核验

本轮实现前基线为 Factory `9604e58`，Braid 起点为 `bd0cfcc`。用户明确不用实验验收；只做无模型测试、构建和只读历史证据核对，没有新模型请求、core probe、Playground 或 bench。

历史 shared-config 方案已退出；活动 variant 直接持有生成入口。显式单核心检查仍要求 `--config`，历史 run 只读回放。list/show、outcome 与 feedback 单独记录 backend；Playground 只读取显式提供的网关/模型配置，不能为 ZIP 切换核心。

Factory 本地 68 项测试通过，覆盖默认配置、Codex 覆盖、自定义配置不回写、旧运行身份和 backend 过滤、失效入口提前拒绝。历史 `pi-svc` run 只读回放仍显示原 9/32；这不是本轮新分数。SVC status 为 healthy，导航与 Corpus 为 current；维护文档链接检查通过。

Braid 提交为 `e0c3ca2`。13 项单元测试和 1 项真实 CLI 集成测试通过，cargo fmt 与 cargo build 通过；新增迁移验证 v3 数据原样保留并升级到 v4。Clippy 退出 101，独立干净基线 bd0cfcc 也失败，主 Agent 对照两份日志确认错误多重集相同；不将它写为 lint 通过，也不在本轮扩大修复历史问题。

主 Agent 定向复核直接创建事务、writer fencing、request-id 重试和孤立分支处理，并补足空列表未知 JSON 字段拒绝与 view --comments。另在临时 Git/SQLite 状态中，通过真实 Braid 二进制运行 Factory 的 preparation_script（仅替换末尾的等待），验证 runtime/external/失效 writer 边界、comment JSON 和 status JSON；直接 pr create 重试不追加事件，hide/delete 正文不可见，PR description 读回一致。该检查没有启动 provider 或模型。

提交后已运行 sources.build('braid') 并通过 require_build：当前二进制、完整源码和 e0c3ca2 HEAD 的 build stamp 一致。修改后的 12 份入口/维护文档链接有效。Factory 与 Braid 分别提交，SVC 源码及安装未更改。

本记录对应的 CLI/config 实施结束时，完整协作链尚未实施。其后的产品讨论已撤回父 turn 让出位置、固定子结果唤醒等提案，当前依据见 design/technical/plan。单一 variant 不表示这些能力已存在，本历史核验不证明后续方案已完成。
