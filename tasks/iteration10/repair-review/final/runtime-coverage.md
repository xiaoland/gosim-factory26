# 最终复审运行时覆盖与版本边界

`实核`表示本轮读当前相关实现并核对接口/定向原文；`复用`表示未变化部分保留前轮有边界结论，不冒称重做独立行为验证。旧最终覆盖见 `coverage.md`；本轮发现和建议见 `runtime-current.md`。方法/装配项由methods分支负责，此表只列本分支相关边界。

| 目录 | 本轮处理 | 判断与限制 |
| --- | --- | --- |
| L01 / R11 / Z01 | 实核完整两variant observer（文件一致）、Pi new/resume替换、原生角色审计的重复委派链。 | 按父历史保留消除FF1同home≠同父的错误；不转移旧任务所有权。未运行startup/resume。 |
| Z02 | 实核observer所有watcher、通知/关闭、Pi sendCustomMessage、Braid settled/writer链。 | 新发现FR1：活着但已settled的父仍会被历史结果独立唤起。旧“存活期转送可接受”不能原样复用。 |
| L02 / A01 | 实核当前PBB patch、既有PBB完成队列实现、锁定Pi agent_end→队列→settled、补丁装配。定向读Sheet349 L30–58。 | 有限job纳入终态及service不独立唤起方向正确；完成/取消/settled行为未验。DB时间/篡改后写成功沿用writer-followup，不冒称本轮重开DB。 |
| L03 | 实核lab evidence ID定位、路径边界、UTF-8尾部、行号与CLI参数；读audit-analytics说明。 | 连续分页目标成立；未执行CLI，不推导跨链语义已经自动完成。 |
| R10 / R12 | 实核observer Unknown agent和subagent_wait追加提示；角色guard/正文复用旧审。 | 提示保留错误且区分Braid所有权与原生工具命名空间；不承担技术终态保证。角色提示采用未验。 |
| R14 / R15 / R16 | Braid相关快照文件未漂移；settled与Idle本轮为FR1实核，其余Context一次性、Deferred及合批复用旧审。 | 不重跑历史协议验证；不把输入接受、临时恢复失败与业务完成混为一谈。 |
| R01 / R17 / R19 / R20 | 无本轮相关Braid源码增量，复用最终coverage及G/S报告边界。 | 消息回执/整理/退订/成员身份属对象能力；未重开DB/CLI，不宣称自然采用。 |
| R18 / R21 | 无本轮相关Braid源码增量，复用默认分支关闭意图、合并恢复、编号/手工整合的有限旧结论。 | 本轮未全读Git发布恢复链，未升级验收。 |
| R23 / R24 / A02 | 无本轮相关Braid源码增量，复用旧地址结清、全范围终态、离线孤儿及首条Wake的有界结论。 | 原生内部工作不交给Braid；离线恢复须先确认旧执行停止。未重开旧DB。 |
| R25 / A03 | 本轮定向读Pi保留终态reason/error；监控其余实现及来源边界复用旧结论。 | 不以token增长作业务进展，不将旧执行错误算当前故障。 |
| R26 / R27 / A10 | helper及对应技能快照文件未漂移，复用旧审的自有process group/首轮退出证据。 | 未运行helper；不扩展到脱离组进程/SIGKILL完整保证，不添加沙箱。 |
| R28 / A06 / A07 | 补丁锁定依赖、runtime.py和Docker补丁接线实核；浏览器/缓存/运行条件复用旧审，方法装配归methods。 | 源码与新包不同层；Node20正式兼容保留真实观察条件。 |
| R29 | Collector/CLI相关旧结论复用；本次analytics新读取入口另列L03。 | 未重发遥测，不宣称SDK成功等于逐条持久化或旧消耗可兑现节省。 |
| Z03 | 实核BodyArgs文件/stdin帮助及读取入口；原shell展开症状沿用Sheet审查。 | 帮助暴露已有可靠入口；不改变shell执行语义。 |
| A05 | Braid测试删除不作新增逐行复审，遵守禁止运行/重建规则。 | 用户范围决定，不包装成质量或分数根因。 |
| A08 / A09 / A11 | G/S审查及旧运行时回执结论作为接口背景复用；方法正文交methods。 | 顺序、保留退出状态、写后读回属于采用义务，不据此新增语义调度器/自动去重。 |
| A12 | 本分支不重复HF文档/API核查。 | 无本次运行时增量；沿用旧coverage的版本限定。 |

## 来源一致性

只读对照 `source-snapshot.json` 中已登记的 `sources/braid/`、`harness/npm/`、agent-browser技能/helper、runtime.py、submission及两活动variant observer文件。该集合只有PBB patch和两份observer发生变化；其余已登记文件一致。这为旧结论的边界复用提供版本依据，不保证未登记文件，也不把哈希相同当行为验证。lab入口是新增范围，另记当前摘要。

| 当前文件 | SHA-256 |
| --- | --- |
| variants/pi-braid/extensions/factory-subagent-observer.ts | c0168d377385d1366980e6cee95d72cf05435a5c804f739a27728ec7a2242afb |
| variants/pi-braid-flash-team/extensions/factory-subagent-observer.ts | c0168d377385d1366980e6cee95d72cf05435a5c804f739a27728ec7a2242afb |
| harness/npm/patches/pi-background-bash-1.0.5.patch | ff7631410d121043d382eaf3671bc31922172cbad67242a5908ab3f298320b38 |
| lab/__main__.py | c91016f406fe6a1e85828c2f67f56237d9866c265eb6855a5e43765523903d0f |

只读文件、比较摘要及写审查文档，没有运行生产函数、测试、探针、构建或实验。未重新全读263会话；Sheet349是为验证生命周期机制的定向原文，官网旧executor链采用已有审计并明确其缺证。原始时间链、当前机制、未来效果分开陈述。
