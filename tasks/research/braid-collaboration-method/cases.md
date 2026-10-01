# 真实案例与改写

本页使用两个历史任务的原始 Braid DB 和 lineage。摘录用于说明信息结构，不把长度、reset 数或某次错误直接归因为得分。I11 的 runtime 与当前 dirty 工作树不同；尤其历史 `resolve <reply>` 会隐式上升到 root，当前接口已经改为只接受 root ID。

## 1. 新 Issue：当前义务被历史和消费者细节淹没

**原件：** GitHub DB `local_items.node_id='issue:6'`，正文 9,293 字符、96 行。

正文同时保存原需求、截图来源、完整 API schema、共享合同迁移、三轮终验、merge 身份，以及 M4b/M6a 两组消费者的逐文件断言。典型片段：

> “本模块交付的 diff/树 API 是 M6a 比较页与 Files changed 的直接依赖……”

结尾又累积 “#7 已获批的契约增量” 五项和 “#9（M6a）同步更新 4 处 Vitest + 1 处 e2e”。问题不是 9,293 这个数字，而是五种不同生命周期的事实没有唯一权威。

**改写：**

```md
目标：交付 REQ-4-1、4-2-1、4-2-2 的文件浏览、历史和 diff。

权威入口：
- 原需求：requirements.yaml 对应节点
- 当前接口合同：docs/architecture.md §7.2、§9.16
- 种子合同：docs/seed-data.md
- 实现：PR #16

完成门：
- 三条需求场景与五个已列反例
- Vitest、全量 e2e、platform-path
- M4b/M6a 消费不破坏 §7.2

状态：PR #16 已合入，merge 4a8f3c9；本项关闭。
证据：PR #16 thread 143 / comment #196。

后续消费者：
- M4b：当前变更决定见 #244/#255
- M6a：seed 边界见 thread 234
```

**删掉/外移：** API 字段表进稳定设计文档；逐文件断言和完整输出留 PR/证据；历史变化留裁决 thread；不在已关闭 Issue 镜像消费者每个新 head。

**保留：** 当前目标、合同入口、最终状态、仍有效的消费约束与证据入口。因为当前 PR 不自动展开关闭关联 Issue 的正文或任何关联 Issue 评论，不能只把这些事实藏在旧文件或旧 thread。

## 2. 契约变化：顶部更正仍背着整套旧方案

**原件：** GitHub comment #89，8,113 字符。

开头已做关键更正：

> “指派/标签/里程碑/关闭重开操作的档次 ‘triage+’ 应读作显式集合 triage/maintain/admin（不含 write）……”

但其后仍保留整套 M5 API、前端、验收和旧实施计划。读者必须自行判断顶部补丁覆盖了下面哪些旧句子。

**改写：**

```md
决定：Issue 管理操作权限改为
{triage, maintain, admin}，排除 write。

替代：#89 原设计中“指派/标签/里程碑/关闭重开 = triage+”的全部表述。

不变：
- 创建/评论/编辑仍为 write+
- assignable-users 仍表示角色至少为 triage

影响：
- PR #15：使用 permissions.ISSUE_MANAGER_ROLES
- docs/architecture.md §4：由根在 #112 更新
- M6a：复用同一集合

下一动作：PR #15 负责人用候选 commit 回执。
```

完整且仍有效的合同写回稳定设计文档；comment 只承担“变了什么、替代谁、影响谁、谁行动”。如果只在 #89 顶部留补丁又 resolve/hide，该更正可能从默认工作集消失；因此当前合同入口必须另有稳定落点。

## 3. 反例与疑问：一个 thread 混了四个结束条件

**原件：** GitHub thread root #308，共 11 条、17,499 字符。原始入口：

- `tasks/iteration11/braid-context-methodology/evidence/continuation-comments.json`
- `tasks/iteration11/braid-context-methodology/evidence/comments-324-327.json`

#308 把 M6b 全套技术设计和 A/B/C 三项裁决请求写在同一 root；之后文档义务、清单外测试失败、暂停改动、批准、局部复核都继续回复该 root。历史 #324 试图 `resolve 318`，实际折叠整个 #308；#325–327 恢复后只能让全部内容保持可见。

正确组织是：A、B、C 各自成为可独立裁决的 root；`content.test.js:161` 清单外失败另开 root；PR thread 只处理候选与验收。

**把 #318 改成独立反例：**

```md
反例：merge-lab 新增 4 个 seed commit 后，
content.test.js:161 依赖全局 id=16 的构造失败。

不变判据：同一 rev 可按 hex/decimal 解释时，hex 优先。

拟改：在 acme-docs 内显式创建一对可达且未占用的歧义 id；
保留两个 unknown-rev 404 断言。

需根裁决：允许把该用例构造加入 #313 的窄改清单吗？
PR #22 在裁决前不提交此改动。
```

这个 root 有一个问题、一个 owner、一个结束条件。裁决后可安全 resolve，不影响长期 A/B/C 合同。

## 4. 交接：关系和通知不等于承接

**正例原件：** GitHub Issue #8 → PR #17。旧 owner 没有因一次消息就关闭责任，而是在具体 PR 接手两个前提、根核实后才关闭。该过程入口见 `tasks/iteration11/braid-context-methodology/content-evidence.md` 与 `tasks/iteration11/braid-context-methodology/report.md`。

**建议写法：**

```md
交给 @pr17-owner：
- 产物：Issue 管理合同 @ docs/architecture.md §4, commit <C>
- 你需完成：把 assign/label/milestone/close 权限切到显式集合
- 完成条件：列出的反例成立，候选 head 与证据回到本 thread
- 我仍负责：Issue #8 的整体完成判断；收到可核候选前保持 OPEN
```

接收者只需回复：

```md
接手上述两项；依赖合同 commit <C>。候选和反例证据回到本 thread。
```

当前 Braid 的 linked relation 不是 subscription，也不表示接受；comment queued/delivered 也只证明送达路径。正式负责人 assignment 与明确回应/正确行动共同形成闭环。

## 5. PR description：合并后仍镜像 25 轮外部状态

**原件：** Sheet PR #9，正文 35,643 字符，revision 67。

后半持续累积：

> “B 无代码动作”  
> “② 的语义改判登记……”  
> “零动作的后续契约增量……”  
> “packet 第 8/9/10/…/25 条……”

它把 E/C 的外部决定、探针、hash、订阅更正和每轮无动作确认镜像到一个已经 merged 的 PR。

**终态改写：**

```md
结果：工作表与行列结构已由 merge <M> 合入。

实现范围：
- 工作表 CRUD 与持久化
- 行列插删和结构位移
- 本模块消费的 insert/delete 引用重写

合同：
- 当前共享接口：docs/...@<commit>
- pivot 最终合同由 E/PR #12 承接；决定入口 #375/#377

验证：
- 所验 head：<H>
- 结果与原始日志：comment #...
- 已知边界：...

本 PR 无剩余动作。
```

“已看到外部决定，但本 PR 无动作”最多发一次带版本的消费回执；不应反复改 description。共享合同的权威是拥有它的稳定文档或 Issue，不是每个旧 PR 各一份。

## 6. PR 准备审阅：表格齐全仍可能绑错证据

**原件：** GitHub PR #23 的 #341/#345/#347，过程见 `tasks/iteration11/braid-context-methodology/final-pr23-flow.md`。

#345 用表格绑定命令、结果、退出码、日志和 head，形式优于散文；但 `auth-restart-isolated.txt` 保存过一次 `1 failed/6 skipped, exit 1`，#345 却把另一次 4828ms 成功绑定到该文件。结构化不等于身份正确。

**ready-for-review：**

```md
Ready for review: f628045
代码 head：0c73f4a；两者除 evidence/packet 外零实现差异。

覆盖：最终整合范围，合同版本 <入口>。

最终证据：
- pnpm test：194 passed + typecheck，exit 0，test-run3.txt，head 0c73f4a
- pnpm e2e：152 passed，exit 0，e2e-run2.txt，head 0c73f4a
- platform-path：152 passed，exit 0，platform-path-run1.txt，head 0e57fd0
  适用理由：后续只改 vitest timeout 配置，该路径不执行它

请审：
1. head/树身份；
2. timeout 改动是否保持断言；
3. 旧 platform-path 证据是否仍适用；
4. 原需求语义覆盖是否充分，而非只看 REQ ID 出现。
```

## 7. 审阅结论：明确已核与未核

```md
Reviewed f628045：acceptable。

已核：
- head/亲缘与零实现差异
- test/e2e/platform 日志及退出码
- timeout 配置未改断言

未由本审阅重新证明：
- 47 个需求节点的行为映射充分性；沿用依据为 <入口>

下一动作：以 --match-head-commit f628045 合并。
```

这比“REQ 都引用了，可以合并”更准确。Braid 当前没有原生 review decision，必须用 comment 明说结论与边界；不能捏造 `pr review --approve`。

## 8. 合并和关闭：不要先写成事实

**原件：** PR #23 #347 先说：

> “Issue #1 以 completed 关闭。”

#348 实际读到 Issue 仍为 OPEN；根直到 #349 执行 close 并得到回执后才真正关闭。完整定位见 `tasks/iteration11/braid-cli-agent-experience/interaction-cases.md` C6。

**状态动作前：**

```md
PR #23 已合并：merge 442dc1c。
Issue #1 当前仍 OPEN；剩余动作：根执行 completed close。
```

**close 成功后：**

```md
已关闭：Issue #1 completed。
交付：PR #23 merge 442dc1c。
验收：test 194/194、e2e 152、platform exit 0。
证据：PR #23 #345/#347；无剩余待办。
```

#349 只有 230 字，却完成了状态、交付、证据和剩余义务的闭环。它是“短且够用”的正例，不证明所有关闭评论都应限制在相同长度。

## 9. hide：重复写操作已经造成两次投递

**原件：** GitHub #256/#257，各 1,438 字符、正文完全相同。11:44:27 写操作成功且三名收件人 queued；Agent 自己用 `head -c 300` 截断回包，看不到 ID，11:44:31 重放 mutation；11:44:54 才 hide #257。

正确恢复协议：写入结果不确定时先按对象、作者、时间或当前成员的最后评论读取状态；不要为取回 ID 重放写操作。确认重复后，hide 重复项并说明 `duplicate of #256`。hide 改善后续默认视图，却不能撤回两组已排队通知。

## 10. 不应过度归纳的数字

| 观察量 | GitHub | Sheet |
| --- | ---: | ---: |
| Issue/PR | 23 | 14 |
| description 当前正文字符 | 69,748 | 191,426 |
| description edits | 186 | 374 |
| comments | 352 | 589 |
| comments 当前正文字符 | 388,017 | 904,879 |
| context resets | 182 | 359 |

Sheet thread #1 有 138 条、222,576 字符；根的一次实际输入达到 167,672 字符。Agent 在这次输入中既正确识别已有 #265/#267 并停止催问，也仍需重新定位旧 thread 和纠正状态。结论只能是：定位、维护和选择成本可观察；不能声称“大输入必然导致错误”或“删掉多少字符就节省多少知识”。

GitHub 唯一的大块 Agent 精确重复正文是 #256/#257；其余大量精确重复是短系统提醒。把所有重复都叫成 Agent 冗余会混淆生产者，也会把 runtime 的提醒管理问题错误推给写作规范。
