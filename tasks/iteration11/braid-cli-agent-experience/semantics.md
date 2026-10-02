# 关键操作的真实语义与版本边界

2026-09-30，主分析只读核实。当前代码位置对应 [source-manifest.json](source-manifest.json) 中的工作区摘要，不能由 Git HEAD 单独复现。以下静态路径没有执行验证。

## 1. 三种证据不能混在一起

| 证据 | 能证明 | 不能证明 |
|---|---|---|
| 当前 `sources/braid`，HEAD `0712a58d0e5f7af225473d6c48c4aa740c20dfbf` + dirty | 当前可见接口定义、调用路径、事务及分支逻辑 | 已编译/部署，或历史 Agent 已有该能力 |
| `runs/iteration11/20260930-completed-turn-resume/build/braid-source.tar.gz`，SHA256 `fa7e91a01c8a6b09ecdb3b2730babebc271cc9f5a4ab3afdbf09b2278675fc28`；已有提取 `../braid-context-methodology/evidence/frozen-src-*.txt` | 该次冻结源码中的语义 | 09-29 所有早期 binary 与它逐字一致 |
| `runs/iteration11/runtime-stalls/build/build-identity.json`：以上 base + `startup.patch`，binary SHA256 `d76d65f133979a9f310b39e73fc254f727b564734ee1513c4febe6fbecb083be`；最终 native | 最终接续的已保存身份与实际命令交互 | 当前未提交改进已被这次运行使用 |

旧启动 binary `3056fe…05bf4` 的身份及失败边界沿用 [runtime-semantics](../braid-context-methodology/runtime-semantics.md)。本次未执行任何 Braid binary，也未下载、安装或重建；早期 Sheet/GitHub 交互由原始输入输出直接作证，不在缺 hash 时猜版本。

## 2. description 自编辑与 hide：失效不等于必然唤醒

当前 [objects.rs](../../../sources/braid/src/objects.rs:867) 的 `edit_with_parent_and_assignees` 在 title/body 真正不同才改写与增加 revision；只有可见文本变化（忽略 HTML 注释的差异，title 变化仍算）才记录 edited、通知关注者、发 Invalidate。相同正文不会因重复调用继续失效；仅 HTML 注释变化仍会持久改正文，但不发这一可见变更事件。

[emit](../../../sources/braid/src/objects.rs:644) 仅将 **本工作项作者的 Wake** 转为 OriginEcho；**Invalidate 没有这项自写豁免**。目标没有 active/materializing/finalizing assignment 时 Invalidate 变 Noop；因此不是所有 hide 都造成会话重建。Issue description 更新还沿关联关系使 PR 失效（[changed](../../../sources/braid/src/objects.rs:693)）；普通父子层级不是同一传播规则。

[hide_comments](../../../sources/braid/src/objects.rs:1152) 只更改指定评论的 lifecycle/reason，整批先校验、去重，在一个 immediate transaction 中提交。与已隐藏状态及原因完全相同不重复改变；修改 hide reason 也可能产生变更。`discussion_changed` 对 hide/resolve 发本项与关联 PR 的 Invalidate，却只对 created/edited 逐收件人发评论投递；**“hide 唤醒”不能表述成“hide 重新给所有参与者发正文评论”**（[1040](../../../sources/braid/src/objects.rs:1040)）。

主分析回读最终根原生：

- `fb383042` → `63a780d8`，02:09:56–59，hide306/328/329 + resolve337 成功工具返回为空；随后 `5b452edd` 明确列出“你的修改”和重建提醒。
- `56f6748a` → `597674e4`，02:21:55–57，Agent 明知重复 hide 增加 churn，仍为一致性 hide339；随后 `d5976318` 收到自己的 hide 重建通知。
- 完整路径/行/toolCallId 保存在 [primary-native-excerpts.json](primary-native-excerpts.json)，对应原索引 R61/62/65、R91/92/94。native `isError=false` 不等于单条 CLI 独立退出码记录；这里用后续通知与状态证据确认发生过写入。

历史源码 `complete_context_reset` 读保存的 `cr.continuation`，在开始重建时已有 running turn 就可能接续；[历史函数逐行提取](historical-reset-completion.txt) 来自以上 tar 的 `braid/src/store/mod.rs:5194`。当前 [store.rs:5231](../../../sources/braid/src/store/mod.rs:5231) 已在完成重建时查询旧 session 最近的非 reset-notice turn，只有 `interrupted/failed/unknown` 才产生 `reset_continuation` Wake。当前 [provider.rs:94](../../../sources/braid/src/group/provider.rs:94) 也按 initial_assignment/reset_continuation/terminal_contact 等区分说明，保留作者和 own_edit。

**裁决：**历史额外工作链已证；当前“self-edit/hide 必然重新要求干活”的缺陷不能成立。已实现方向需要后续获授权运行核实，不能重复立项修同一处。本轮接口仍应说明“可见性变化会影响后续上下文”，回执准确报告持久变化/失效登记，不预测异步 Agent 一定醒来、理解或采取行动。也不建议为了减少回声跳过必要失效，防止仍使用旧正文。

## 3. resolve 是整 thread 的时间边界

当前 [objects.rs:1185](../../../sources/braid/src/objects.rs:1185)：

1. 任意评论 ID 解析为 `thread_root`；多个输入属于同根时去重。
2. resolve 将 cutoff 设置为该 thread 当前最大 comment_id；不是传入 ID，不是子树，不是“这个问题”的语义范围。
3. cutoff 以内为折叠历史，之后新回复仍可见，root 的 resolved 标志仍可为 true；不能用单个 `resolved` 布尔值当整串全部结束。
4. 重复 resolve 在没有新回复时 unchanged；有新回复时会推进 cutoff。因此**对状态固定才幂等，面对新回复不是安全的盲重试**。
5. unresolve 清掉整个 root cutoff；不等于恢复上一次 cutoff，不能把它当精确 undo；独立 hide/delete 不受恢复。

当前已新增 `CommentResolution {thread_root,resolved_through,affected_comments,changed}` 与[文本回执](../../../sources/braid/src/cli/mod.rs:696)，help 已说“整条讨论”。尚无 preview、调用方固定 cutoff 或 JSON resolve 回执。`affected_comments` 统计 cutoff 区间内所有记录，包括本已 hidden/deleted 的记录；不能把该数宣传为“此次新增隐藏的可见正文数”。

当前[单条读取](../../../sources/braid/src/objects.rs:1311)会展开 resolved 的 visible 正文；`--thread` 默认不展开 cutoff 以内历史，`--include-hidden` 同时展开 hidden/resolved（deleted 无正文）。单条 view 内部仍加载所属 thread 后 retain 目标，不意味着后端只查一条。读取结果中 `body:null` 应结合 hidden/deleted/folded 判断，不能自动等于“作者发了空评论”。

两题误用属于**业务意图粒度与工具操作粒度不一致**，同时有界面缺口与方法问题。保留整 thread 语义、提前显示 cutoff，并按独立闭环议题开 thread，是小范围方案。新增子树 resolve 会改变投影、线程状态和恢复规则，证据尚不足以要求此产品变更。

## 4. 关系、关闭和合并

| 操作 | 实际含义、可确认事实 | Agent 容易越界的推断 |
|---|---|---|
| Issue `--parent` | 层级引用，检查循环；不递归注入父正文（[set_parent_in](../../../sources/braid/src/objects.rs:912)、既有 runtime-semantics） | 有父链接就已交付完整需求 |
| PR `--issue`/link | N:M 背景关联；重复相同 link 无变更；改变关联通知关注者、使 PR 上下文失效（[1660](../../../sources/braid/src/objects.rs:1660)） | link 等于 closes，或关联 Issue 的全部讨论总会注入 |
| PR 正文 `Closes #N` | 合入 origin symbolic HEAD 指向的默认分支时解析关闭引用；冻结到 merge intent；不要求先存在 association（[1837](../../../sources/braid/src/objects.rs:1837)） | unlink 必定取消关闭意图；合入 develop 也必然关闭；改正文没有生命周期副作用 |
| issue/pr close/reopen | 状态+可选评论同事务；重复目标状态 unchanged 且不再发表评论；MERGED PR 不可 close/reopen（[1760](../../../sources/braid/src/objects.rs:1760)） | description 写“已关闭”就是 closed；close reason 可当自由解释；close 证明应用验收通过 |
| pr ready | 草稿状态与当时 published head 的观察；不等于评审/验收通过，后续 merge 不以 ready_commit 当冻结候选（[1709](../../../sources/braid/src/objects.rs:1709)、[1864](../../../sources/braid/src/objects.rs:1864)） | ready 已经锁定将合并的内容 |
| pr merge | 即时本地合并已发布 origin ref；`--match-head-commit` 阻止合并未经审查的新 head；durable intent + Git ref 条件更新弥合 SQLite/Git 分界 | 本地未 push 文件进入合并；返回 commit 就说明所有 Issue 都关闭；所有成功都写了 Git ref |

当前 merge 有三种成功路径：新合并、已 MERGED 重读原回执、确认目标已含已观察的独有 head 并登记整合。CLI 一律仅返回 `merge_commit`，所以调用者不能仅凭返回区分这次是否写了 ref，或哪些 Issue 因正文关闭。[1868](../../../sources/braid/src/objects.rs:1868)、[1900](../../../sources/braid/src/objects.rs:1900)、[CLI 1105](../../../sources/braid/src/cli/mod.rs:1105)。已 MERGED 的重复调用先返回保存 commit，不再校验传入的新 expected head；这是查询既成结果，不应描述为本次又通过 head guard。

失败也不都代表零副作用：合并冲突先保存 conflict intent、登记 Wake 再报错；prepared intent 可能已提交，Git ref 可能先于后续 DB 完成。错误回执应区分“业务目标未达成”和“没有任何持久变化”，保留源/目标 ref、commit、具体错误与可安全继续的入口（[1940](../../../sources/braid/src/objects.rs:1940)、[1980](../../../sources/braid/src/objects.rs:1980)）。这里是源码边界审查，没有制造冲突运行。

## 5. 并发与重试：已存在保护和真实缺口

- 已有：SQLite immediate transaction；身份绑定当前 native 执行、改派 fence 旧 writer；assignee 候选在事务内重新认领，过期拒绝不静默换人；close+comment 原子；PR create `--request-id`；merge 精确 head 条件及 ref 更新/恢复。
- PR request-id 是运行内精确键，重复返回原 PR；显式不同 base/head 拒绝，其它标题/正文/关联/assignee 不更新（[1548](../../../sources/braid/src/objects.rs:1548)）。不能当 upsert。回包应说 replayed，避免把新正文当成已应用。
- Issue create、普通 comment create 没有调用方重试键。评论成功落库而回包丢失后直接重试可能重复发言/通知，历史 #256/#257 的具体机制另由案例判读，不能仅凭重复就归因网络重试。
- 普通 description edit 是整体替换；事务防止交错写坏 SQLite，却没有校验 read→edit 间正文版本。并发编辑可 last-write-wins。这里证明缺少前置条件，不证明历史某段正文丢失由并发造成。
- `--edit-last/--delete-last` 目标先查后另开写事务（[CLI:749](../../../sources/braid/src/cli/mod.rs:749)），是依赖作者/时点的便捷功能。Agent 已有 comment ID 时应优先精确 ID，保留 last 模式但在帮助说明范围，不靠它提供幂等性。
