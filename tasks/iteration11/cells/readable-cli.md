# I11 可读协作界面：优先级 1、3

状态：源码已改，未部署，尚无新 variant 运行效果证据。本单元只处理 I11-04 的时间线与重建来源、I11-06 的指定评论读取；不处理 I11-03/05 的消息及后台生命周期，也不改变当前 I10 运行。

## 问题、根因与修复

| 问题 | 根因 | 已实施 |
| --- | --- | --- |
| `issue/pr view --timeline` 默认 30 条只显示最早一页，容易被当成全部历史 | `LocalObjects::timeline` 恰好取 `limit` 行；CLI 原样输出行数组，没有截断或下一页事实 | 多取一行判定 `has_more`，只显示请求的数量。文本给出当前 `--after` 游标、是否还有记录和下一页完整命令；JSON 给出 `items/after/limit/has_more/next_after`。游标使用实际末条的全局 `ordinal`，不按行数推算。`--after` 必须非负。Issue 与 PR 共用一个入口。 |
| 指定 `comment view 101` 在 resolve 后正文为 null，只剩折叠元数据与投递回执 | 指定读取和 `--thread` 浏览都调用同一折叠投影，`include_hidden=false` 时无差别隐藏 resolved 历史 | 指定读取展开仍为 visible 的已折叠正文；`--thread` 和工作项历史仍折叠。独立 hide 继续隐藏，delete 不能恢复；正文未展示时文本和 JSON 都给出 `comment view ID --include-hidden` 的明确操作。 |
| 自编辑后新会话只看见泛化“有更新”，不知是谁写入、为何重建、快照是否已含变化 | reset 已绑定 `context_reset_events`，事件有 `writer_group/turn`，但 `ContextResetClaim` 只提取 `reference`，新 session 只接收对象快照和泛化 continuation | 从已绑定事件关联写入成员并比较 reset 当前 agent；旧会话通知及新会话 Context 前缀列出作者、是否当前成员写入和事件变更引用。前缀说明下方完整对象快照在这些事件提交后读取，显示读取时的当前可见状态。未记录作者不猜测身份。保留原有自编辑 continuation、hide/resolve 失效与重建流程。 |

来源提示不宣称历史正文仍原样存在，因为后续编辑、隐藏或折叠可能改变当前投影；它也不声称证明模型已理解通知。`context_revision` 继续取完整对象投影哈希，重建来源前缀不改变对象版本；实际传入新 session 的完整文本另核硬字节限制。

## 依据与调用链

- `run-audit/sheet/report.md` 第 3–4 节：07:48 自编辑 reset `01a0ec22-946c…` 的新会话已含新正文，却重复调查；PR8 的 #101 在 resolved 后默认指定读取为 null。
- `src/cli/mod.rs` 的 Issue/PR view 共同调用 `print_timeline`，comment view 调 `LocalObjects::view_comment`；`src/objects.rs` 的 `read_comments` 同时为 CLI 和 Context 投影服务，故只在直接指定读取时展开 resolved 可见正文。
- `src/store/mod.rs` 的 `begin_context_reset_transaction` 把事件绑定到 reset，`load_context_reset_claim` 读取；`src/group/provider.rs` 渲染通知，`src/group/dispatch.rs::materialize_context_reset` 创建新 session。现有事件元数据足够，不加迁移。
- 对审计只读数据库查询该 reset 的两条事件，均为 `issue #1 title/body 已修改`、作者 `glm-1`，且 `writer_group` 与 reset agent 相同。它说明所加来源可从原始元数据得出；不代表新运行行为已验证。

## 验证与边界

`cargo check` 与 `cargo build -q` 均通过；只有原仓库已有的 dead-code warnings。`git diff --check` 通过。将审计保存的 SQLite 数据库复制到临时目录后，用新 CLI 作实际只读操作：`issue view 1 --timeline --limit 3` 显示 3 条与下一页 `--after 3`；JSON 的 `has_more=true,next_after=3`；`comment view 101 --json` 直接显示已解决但仍 visible 的正文；`comment view 101 --thread --json` 仍将 #100/#101 折叠并给读取命令。没有运行测试/Harness、没有启动或部署 Braid、没有触碰 I10 运行；新 variant 对模型推理和耗时的效果仍须由真实运行判断，233.803 秒只是审计样本，不能当节省承诺。
