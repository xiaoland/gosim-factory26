# 仓库布局与维护边界

2026-10-07 已按用户“好的，开始改造吧”授权实施。[审计](audit.md)保存实施前的观察；当前状态、验证范围与交接入口见 [packet.md](packet.md)。目标是降低找答案、辨认历史条件和同步消费者的成本，目录数量只描述结果。

## 当前布局

```text
variants/                   独立 Harness 实现与原生角色
materials/                  共享技能、npm 依赖、补丁、模型 catalog 与配方
tooling/
  scripts/                  公共装配、打包、原生执行支持和模型网关
  linux/                    Linux 资源构建、checkpoint 与恢复支持
consoles/
  braid/                    协作对象、讨论、审阅与原生会话界面
  lab/                      通用 run、资源、费用与评测界面
  package.json              共享依赖，分别构建两个产品
lab/                        执行设施、ARC 接入与证据分析
  exp/                      旧冻结 experiment/job/attempt 合同支持
sources/                    Braid、参赛 SVC 与 model-proxy 的独立源码
experiments/                实验定义；hackathon-local/suite 为公开应用验收集
docs/                       持续维护的产品、技术与操作说明
tasks/                      问题、授权、方案、接续点和调查结论
runs/                       执行与调查证据集合
  reports/                  Git 跟踪的历史报告及集中索引
third_party/                本地外部依赖和历史工作树，Git 忽略
```

非隐藏一级目录从审计时的 15 个收敛到 11 个。根级 README、AGENTS、CONTRIBUTING、Makefile 和配置继续承担入口职责。隐藏环境、凭据和 bootstrap 目录有实际消费者，不为视觉统一而迁移。

## 职责与消费

原 harness 内容是可选择的共享材料，不是 Harness 实现，因而改称 materials；variant 的原生 agents 保留。原 scripts 与 submission 收入 tooling，但分别保留宿主支持与 Linux 交付边界，不同时承诺依赖解耦。公开应用验收集与 hackathon-local 配方相邻，仍是独立评测输入。

Braid Console 和 Lab Console 是两个产品。Lab 嵌入 Braid 原生视图、服务共同挂载，不改变其归属；sources/braid/viewer 与 lab/serve.py 继续各自维护原生投影与 HTTP 挂载。两个界面各有 App、路由、类型、构建配置和 dist，共享 consoles/package.json 与 lockfile，避免重复维护依赖。旧 Braid prepare 只消费 consoles/braid/web/dist，Lab 消费 consoles/lab/web/dist，不再把 Lab 页面交给 Braid API。具体操作见 [Console 入口](../../consoles/README.md)。

reports 迁入 runs/reports，保留文件名、条件与集中索引，不为跨 run 或文档报告创造实际 run 身份。Git 只允许 runs/reports 例外；其余日志、应用、机器状态和制品继续忽略。默认 rg 搜索通过 .ignore 隔离历史报告及已确认的源码、技能和机器回读快照，活动 packet 与结论保持可发现。明确历史查询仍可直接读取路径或使用 rg --no-ignore。

旧 lab.exp 的 compile/build/doctor 只在旧合同文档中推荐；当前运行入口使用实际存在的 Lab 命令。过期推荐与重复 Variant 条目已修正，而不是仅靠隐藏旧文档。废弃根 agents 和 docs/agent-guides 删除，维护引用清理，冻结 JSON 的历史路径保留。

## 身份与保留约束

源码迁移同步 Python import、根路径深度、远端源码选择、公共装配、CLI/Makefile 和维护链接。包内 data/harness、内部 submission 和 Docker context 的 harness/npm 属既有交付合同，不能因源码改名无差别替换。已有 ZIP、manifest、执行器快照和 provenance 不改写；新装配按当前源码生成新的身份。

local-generations 的两份 recipe 与四份公开需求文件迁入所属实验 evidence，字节保持一致，映射见 [任务记录](packet.md#材料迁移记录)。历史 readback 不改写。三个确认失效的本机 PID 文件删除；日志、远端状态和运行材料不据年龄或大小批量回收。运行部署、模型与官网执行不属于本轮改设施授权。

## 反馈范围

验收使用实际构建、CLI、编译、公共包与冻结执行器源码装配、临时本机服务的 HTTP 操作、链接及历史来源回读，不引入 Factory/Braid 测试。构建与空注册表 HTTP 能证明入口和静态资源配对；不能证明真实运行的协作流程、部署更新或模型执行。默认文件候选与查询命中数描述本次静态检索，不宣称模型 token 或耗时收益。
