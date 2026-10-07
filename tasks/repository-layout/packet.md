# 仓库导航与材料收敛

## 当前状态

2026-10-07 开工，2026-10-08 审计、改造与验收完成，本任务变化选择性提交。当前布局见 [design.md](design.md)，实施前证据见 [audit.md](audit.md)。非隐藏一级目录已收敛为 11 个；当前入口纠错、有限检索隔离、两套 Console 构建、材料落点与源码消费链同步完成。

## 开工与负责人

用户授权：“好的，开始改造吧”；随后“你可以自由提交”。主 Agent 负责材料、工具与公开验收集迁移、导航内容及整体集成；layout_consumers 持续负责 Console；audit_materials 持续负责报告、检索边界及本机材料整理；advisor 解决两产品共享构建依赖的取舍。提交仅包含本任务改造，保留其它工作区修改，不 push。

## 目标、用户决定与授权

2026-10-06 用户提出：“当前项目的一级目录下内容太多了，而且也有一些命名不精确（比如 harness/ ）的问题，我们看看怎么整理、收敛一下”。目标是让职责、维护输入和机器产物更容易识别，减少理解与修改成本；不以一级目录数量代替边界判断。

2026-10-07 用户澄清：“我没说不能移动，我只是说，不能移动到 lab/console，这是对 braid console 和 exp/lab console 理解的不准确”。Braid Console 可以移动，但不能由 Lab 挂载关系推导其产品归属。已撤回整包归入 lab/console 和强制保留一级目录两项推断；consoles 下并列两个界面已采用。

用户直接授权：“reports 也不应该属于 docs，因为 docs 存放 durable docs；其实 agents/ 和 docs/agent-guides 里面的内容已经没用了，可以删掉（包括引用）”。这项删除已实施，variant 内的 agents 不在范围内。随后用户将任务扩展为“进一步优化导航性能、可维护性、可读性，进行精简、清理（从文档、代码到产物、运行）”，并问 reports 能否并入 runs。推荐 runs/reports，保留 Git 跟踪与独立搜索边界；迁移已实施。

审计授权为“好，推进审计（注意先规划、理解问题，找到几个关键方向、杠杆点，再分别深入开展调查、审计）”；随后用户“好的，开始改造吧”覆盖审计推荐的实施，“你可以自由提交”覆盖本任务提交，不包括 push。

## 实施结果与证据

harness → materials、scripts → tooling/scripts、submission → tooling/linux、benchmarks/hackathon → experiments/hackathon-local/suite；Braid 与 Lab 界面分别进入 consoles/braid 和 consoles/lab；reports → runs/reports。删除废弃根 agents 和 docs/agent-guides 及维护引用，保留 variant 角色。更新实际导入、根路径、远端源码选择、冻结源码闭包与公共包装配，保留包内合同。

当前运行推荐与旧 lab.exp 合同分开，Variant 索引重复条目删除。默认搜索隔离已确认的 I10/I11 源码、技能、编译快照与机器回读，不整体隐藏活动 tasks。材料负责人两次采样之间默认候选从 5175 减至 4588；同期存在其它修改，因此这是静态样本，不是独立性能实验。报告索引与原始证据可通过明确路径追溯。

所有实施产物位于 WorkSSD 的 `runs/repository-layout/implementation-20261007/`。baseline.json 保存开工 HEAD 与脏工作区，before 保存迁移前材料；materials-map.json、console-moves.json、public-assembly.json、executor-source-assembly.json 保存映射和实际装配证据。

实际反馈包括工作树与提交候选的两套 Console 构建、两套临时本机服务的首页/API/JS/native viewer HTTP 操作、CLI 帮助、Python 编译，以及 I14/Pi variant 材料和公共包装配。临时服务已停止。选择性提交候选还单独编译了 99 个 Python 文件，实际冻结 runner/controller 源码分别为 39/65 文件，冻结 controller 的 CLI 帮助可用；它与含其它未提交改动的工作树装配分别取证。初次 DX build 不带 --variant-only 被拒绝：`DX builders only produce variant material; use Lab public assembly`；I14 选择共享 skills 时缺少 context7-docs/SKILL.md，改用已有冻结完整技能集合后成功。这是输入选择条件，未增加缺失材料 fallback。

HTTP 使用空注册表，未验证真实运行协作。未运行 Factory/Braid 测试、模型或官网评测，未控制既有服务或远端运行，未热部署和批量 GC。技能与原始初始交接文档字节不变；冻结 JSON、原 provenance、历史制品不改写。Git clone 不携带被忽略的运行原件，交接仍须单独传递所需 evidence。

## 材料迁移记录

两份 recipe 从 `local-generations/` 迁入 `runs/iteration14/overnight-20261003/evidence/recipes/`；公开需求从 `local-generations/public-requirements/github-a2-8a282da5502e/` 迁入同一 evidence 下 `public-requirements/github-a2-8a282da5502e/`。历史 example-intent 与 readback 中的旧路径保留；复用时先按此映射定位，不把历史绝对路径当成当前可执行输入。

| 文件 | SHA-256（迁移前后相同） |
| --- | --- |
| experiment27-resourcefix-cleaner.recipe.json | `5da5215b2c33dfcff56311773e253f8af863f7abcae44e678cbb242b85495100` |
| experiment27-resourcefix-reviewer.recipe.json | `23174b642f25a0dd3f7bf90563a3c689a531ddecc44afec65d06902b483097b6` |
| prerequisites.md | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| provenance.json | `ddce7298c60a84fbdd8e36c07c0ce59197232dba7d867349c66fabf564a78af1` |
| requirements.md | `f26ecc05a5b616bd504f94f62a046ab5478a995f822cd3de891df9da0cf4353d` |
| requirements.yaml | `9480921cb3b7ffdc5f32cb76011ecc1d5bf9bfbf2cba38e3a092355ac88a54f8` |
