# 方法与装配反向对账

本次从已应用记录与当前材料反查目录，不再从目录出发宣称完整。结论是：`implementation.md`、`closure.md`和三个`cells/`登记的当前方法/装配改动均能映射到R/A/M项，未找到一项明确已应用却完全无目录承接的新方法修复；但这不等于整个iteration10无遗漏。活动variant与SVC技能没有可用于本轮逐行差分的独立基线，部分装配支持材料此前只有有限核对，须保留如下边界。

本轮只新增本文件，未改实现、运行测试/探针/实验或提交。七技能正文结论复用`methods-current.md`与`methods-coverage.md`，没有重新全读或重做两题归因。

## 已足够核实的改动映射

| 从改动记录出发 | 目录承接 | 独立核对与剩余边界 |
| --- | --- | --- |
| 根先形成设计/判据，根基础直接PR，子项自包含来源与初态，PR计划/预演及整合职责 | R02–R05、R08、R22 | 前轮完整读run.py相关prompt、RUN_CONDITIONS及五主指令；本轮与implementation/closure反向对应，无漏项。实际模型采用未验。 |
| 派生权威、用途迁移/旧豁免、重叠规则、同属性视觉反证、原动作退出结果、成功前置、资源归属及外写读回 | R04–R07、R26–R28、A08–A11 | 七技能相关正文已实核，GitHub原生L23与Sheet原协作正文定向回看；本轮不重复，见methods-current。 |
| advisor咨询前移、所有权/角色名区别、fresh角色公共条件、vision分类读图、explorer工具知识归角色 | R02、R09–R13、A04 | 五profile对应角色全文/一致性已核；completion guard/observer真实机制由运行时分支承担，不以提示词替代。 |
| pnpm/portless、Vitest/Playwright、组件/图标/UnoCSS、官方脚手架、SQLite/事务/初始化、同源API/schema、缓存与正式Node20/npm协议 | A06、A07 | 本轮逐项对`toolchain-proposal.md`与RUN_CONDITIONS；未发现被排除的两题新增建议、TS/Vue强制或预写应用。打包环境和正式应用实际兼容仍不是方法审查证明的事项。 |
| agent-browser named close与结果包装、HyperFormula DetailedCellError纠错 | R26–R28、A10、A12 | 目录已承接；helper机制归运行时线，A12仍复用前轮官方类型出处核对，未把其扩大为整个领域技能已审。 |
| documentation独立技能、检查金字塔、七技能案例、规划正文与模板导航 | M01–M04 | `cells/svc-method-views.md`登记项与前轮直接读取的实际材料一致；无遗漏的新第八技能。 |
| 结果/全过程双路径、单一账本、有界阅读与模型分工 | M05 | `agents/run-analysis.md`及其复盘来源已完整读，采用/节省未证。 |
| cells/writer-followup与audit-analytics | L02、L03 | 非方法新增实现，已有运行时承接；不能误算为本分支全核。 |

## 本次补核的装配支持面

这些不是新发现的产品缺陷，但此前“角色/技能装配已核”的表述容易让读者以为相关配置全部运行验证过。本次补充静态来源核对：

- 五个`profile.json`、`settings.json`及`models.json`的模型ID对应关系：pi-braid为GLM/DeepSeek成员，Flash为GLM/Qwen3.6 Flash/MiniMax M3，原生advisor仍Kimi K3、explorer/executor仍DeepSeek Flash、视觉角色仍视觉模型；所用ID均出现在所属home模型目录。settings均为空packages并关闭内建subagents。该检查只排除当前显见的模型目录缺项，不证明供应商、流式工具或实际返回可用。
- 两个`tools/mcporter.json`内容一致，含Context7、Exa、Handsontable服务；`run.py`把对应variant路径放入MCPORTER_CONFIG，assemble复制tools目录。R13已有归属修复，本次补齐配置文件到fresh进程公共环境的静态路径；未访问远端服务或验证其schema/凭据。
- 两run.py此前仅VARIANT不同，`main.py`提供源码/support入口和存在manifest时的校验入口；技能由build选择、assemble/copy_skill物化、run再次选择并以`--skill`启用。当前源链可解释，不等于任何旧ZIP已包含它，更不等于最终Linux制品内容已经反查通过。

模型选择和settings属于继承装配，不宜为凑目录项另编一个已证历史根因。若主线保留“完整材料核查”表述，须把上述基线配置显式列为“静态补核、来源历史未独立分界、实际调用待观察”，而不是藏在R09“advisor可用”一句中。首次有意义的真实咨询仍需观察请求模型、上游、工具往返、返回与父消费；原`evidence-consumption.md`和角色审计已经要求这一点，本次不新增探针义务。

## 仍不能宣布完整的范围

1. **本轮差分身份不足。** Factory HEAD为`ad0a627…`，两个活动variant整个目录均untracked；SVC HEAD为`b5a0fb8…`，`skills/`整体untracked，其dirty同时包含旧顶层Corpus、CLI、模板/测试删除。`tasks/svc-corpus-review/implementation.md`明确旧CLI安装/ZIP是历史快照，后继skill迁移另属阶段。因此不能把所有dirty当iteration10，也不能仅凭commit ID称已覆盖本轮每个改动。当前能保证的是“登记改动→当前材料→目录”有界对应。最小补证是使用实际开工/冻结材料快照界定差分；没有快照时，应明确记为来源未分界，而不是要求补造历史。
2. **装配不等于依赖内容全审。** 主会话还选用了hyperformula、handsontable、Better Auth、organization、accessibility、ponytail、impeccable、agent-browser。这些继承技能除R/A指定修改外，没有在本轮逐篇复审；也没有证据说明全部内容都属iteration10新增。当前用户否决“两题专属新库建议”不等于要求删除已有领域技能，`toolchain-proposal.md`已明确此边界。若冻结差分显示其中另有本轮改动，应只补审那些改动及受影响入口，不能以七SVC已审代替。
3. **恢复入口和制品采用未在本分支闭合。** 本轮补的是正常generate装配。冷恢复使用哪份冻结材料、runtime/skills/配置是否同版，以及模型预算、provider协议、observer/PBB时序属于运行时/构建线；本分支不以两份run.py相同宣称所有恢复入口一致。原closure与build明确旧包不代表当前树，继续保留该限制。
4. **旧控制页时态不是当前事实证明。** closure仍含“Sheet尚未完成”“F2仍需收敛”等历史段落；最终packet/current-scope与后续implementation已记录其后状态。新增M项也主要在final/current-scope与cells，不应要求读者只看旧29项closure就推断全量。这是控制入口的表述/同步缺口，不是需重做实现的遗漏。主线最终总报告应统一指向当前范围和本次边界，历史记录无需伪装成最新状态。

上述边界不构成新增确定运行缺陷，也不自动要求重开全部历史审计。当前方法修复已足够作文本/职责/静态接线判断；在获得差分来源或新的真实反证之前，继续添加同义提示词并不能弥补“完整性”证据缺口。
