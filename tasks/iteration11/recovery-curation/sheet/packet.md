# I11 Sheet 副本接续整理

状态：已在 Mac 可编辑副本完成最小语义摘剪，独立 curated SQLite 已交封包负责人；原 I10 Sheet 容器仍暂停，未修改原始归档、原运行、应用代码、Git、原生会话，未启动模型或运行检查。本文描述接续入口与已经观察到的证据，不替代最终验收。

## 来源一致性

- 原运行：WSL 的 f26-continue-a2ce3ac2d41459，docker inspect 显示 Running=true、Paused=true；Braid run 为 20260929-042409-811f18d4。
- 暂停原件的 braid.sqlite3 与 braid.sqlite3-wal SHA256 分别为 5a03046078327f63b07e99cc5b517ea0f5fb7c7e5702a53f3c9f97c7ded50a0b、15ad4ef64701a8c032900246427ee351617bd6b7938d7e0829a0dfb51c30d0af，逐字节等于原始 tar 中的对应条目。
- Mac 编辑前副本已经将 WAL checkpoint，主文件字节不同；但与原件的 SQLite iterdump 全量逻辑 SHA256 同为 658fb2af244f577837148b8f8805c4f86840ed4efa25991e613eb7fc3be38610，quick_check 均为 ok。故本次不是从旧采样状态重新整理。
- 原始 tar 在 runs/recovery-curation/original-archives/sheet-template-20260929-042409-811f18d4.tar；编辑目标仅为 runs/recovery-curation/editable/sheet/template/.factory26/20260929-042409-811f18d4/braid-state/braid.sqlite3。

## 当前可复核事实

根 Issue #1 OPEN；Issue #3/#5/#6/#7 CLOSED，Issue #4 仍 OPEN。基础 PR #2 与 A–E 的 PR #8–#12 MERGED；最终整合 PR #13 OPEN、负责人 @deepseek-14。origin/develop 为 d07dd626618b807774327d77c4a71d56e7bb1ef9，origin/main 为 2914d2ddf2a9cc5723619fd2cef53f5b21b8c3ac。d07dd62 相比 E 合入点 ca69b7b 只增加 e2e/integration.spec.ts 与 tasks/pr-13-integration/packet.md，PR #13 工作树干净；这不是 main 交付。

PR #13 持久证据目录 braid-state/evidence/pr-13-integration/final-d07dd62-full-e2e-nonskip/ 的 result.json 绑定 d07dd62、Node 20.19.3、dirty=false、untracked=false、检查退出码 0；check.log 为 68 passed。早期 ca69b7b 全量 64 passed、集成用例定向 4 passed 是不同候选/形态。最终候选的 SKIP_FRONTEND_BUILD=1 全量 E2E、单测/typecheck、平台路径及重启持久、交接回执、精确 head 合并到 main 仍未见完成证据，不能把 68 passed 写成整体通过。

Issue #4 的 B 实现已随 PR #9 合入 15abbf6；其跨 C 回归见 #187，跨 E 回归见 #551 的 develop 真树检查和 #558 的负责人验收。PR #13 #566 把该证据清单计数更正为 12/12。Issue #4 保持 OPEN，待最终整合后显式收口；不能因 B 回归已报结而伪造关闭。最后交付顺序是补齐 PR #13 的其余门禁，按被验 head 合并、核 main 树和应用启动，再由负责人收口 Issue #4 与根 Issue #1。

需求权威仍是 input/requirements.yaml 的 24 条 ATOMIC 描述。根 Issue 的 D1–D3、共享契约 v1→v1.6、B 位移和 D paste 尾扩张分工、C 公式引用重写、E 规则 gate 和 pivot 空 range 哨兵等有效裁定保留在精简正文的导航与历史评论中。参考图只辅助视觉，不替代英文可访问名称和逐字错误文案。

## 实际离线修改

在一次 SQLite IMMEDIATE 事务中，仅更新三项 local_items.body，各将 revision 加一，并各新增一条 actor=external、action=edited 的 local_activity，标明离线 I11 Sheet 导航整理。没有创建 events/wake、关闭 Issue、合并 PR、调整 assignment，也没有修改任何评论。原始长正文与全部评论仍在原始 tar；此次不 hide 评论，因为近期的更正、验收依据和责任交接互相依赖，未确认哪些只属无信息重复。

| 条目 | 改前 revision / 字数 / 正文 SHA256 | 改后 revision / 字数 / 正文 SHA256 | 处理与依据 |
| --- | --- | --- | --- |
| Issue #1 | 46 / 12197 / 536b0c96a9bb8640ae25e8593946e87580b2caa28d67c37a176088027ba19ef4 | 47 / 3412 / 06a454234a5352776f343e1bc653b1055e4eac8ab86a616a76b6cda7166e7f06 | 清除旧的 E 待合入与重复进度，保留 D1–D3、权威需求、共享契约导航；写明 PR #13 和未决门。 |
| Issue #4 | 24 / 9064 / cae0b82a2831f05dc1b45f8e75260b2475b0a56b8730caed0ee94a97a62b0e72 | 25 / 2729 / f7cdaef60bf0c107d0bbbead620f76eb7dd7c72bc10805bddc7be626ef798d41 | 保留六项 REQ-2 交付语义和 B/E 最终哨兵口径；区分回归已验收与 Issue 仍 OPEN。 |
| PR #13 | 1 / 2223 / 0d05a76e16b2fd7d96228de9ad4c9c08c896f22e6c70ac197d6f91ae23a98f5e | 2 / 2797 / 5495cc9b947132207a7eba05d349bac682d786968ce143118cd02333ec1a228e | 更新 head 到 d07dd62、B 回归已结案和 68 passed 的精确范围；原整合验收清单仍保留，缺门明确待办。 |

独立 SQLite backup 输出：/Volumes/WorkSSD/Development/factory26/runs/recovery-curation/curated/sheet/braid.sqlite3，7,647,232 bytes，SHA256 0550d510afbc885176de6464f87535da98eb2337f3a7aebf5f6c43c14502f183。backup 已完成 WAL 内容整合，目标无 WAL 文件依赖；quick_check=ok，三条正文及 revision 在目标复核一致。封包时仅把该文件替换到 WSL 的新 Sheet 独立副本，并移走副本旧 DB/WAL/SHM，不能覆盖暂停原件。
