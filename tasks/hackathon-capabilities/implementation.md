# 实施准备与开工范围

状态：技能取舍、SVC 拆分及本实施范围均已获批准；源码与打包材料已完成，真实实验验收待后续授权。
原生加载接口见 [接口证据](rehearsal-native.md)，独立使用路径预演见 [计划预演](rehearsal-plan.md)。

## 文件布局与内容归属

参赛侧 `sources/svc` 改为一个技能集合，每个目录自身符合 Agent Skills 布局。
开发侧 `~/Development/svc` 和 `.venv/bin/svc` 不在本次范围。

```text
sources/svc/skills/
├─ svc-task-packet/
│  ├─ SKILL.md
│  ├─ references/       planning、information、growth、delegation
│  └─ assets/templates/
├─ svc-investigation/
│  ├─ SKILL.md
│  └─ references/       workflow、debugging、delegating-investigation
├─ svc-design/
│  ├─ SKILL.md
│  └─ references/       workflow、product、technical、engineering-judgment
├─ svc-implementation/
│  ├─ SKILL.md
│  └─ references/       workflow、delegating-implementation
└─ svc-verification/
   ├─ SKILL.md
   └─ references/       check-design、interpreting-results
```

每个入口带核心方法与明确适用问题；正文较深时才链接同目录 references，不把每个入口做成又一张必须转跳的空目录。
同一方法只有一个当前正文来源。
技能之间以可选能力名称介绍后续需要，不使用越出技能目录的相对文件链接；单独复制一个技能仍能理解并使用其核心方法。
模板留在 task-packet 中，因为它们服务于任务材料组织；设计、验收技能不要求另一个技能存在才能工作。
通用委派方法放 task-packet 的可选 delegation 资料；Explorer/Executor 的具体委派方法分别归 investigation/implementation，不增加第六个角色技能。

将当前根 `SKILL.md`、references、assets 的现行内容迁入新归属，删除旧运行入口。
同步 SVC 的 AGENTS、README、CONTRIBUTING、USER_MANUAL，说明集合安装和独立选用；继承的 CLI 与开发历史文件不做顺手清理。

## 历史消费者

已核实三个归档团队 variant 和 native-hackathon 仍读单技能 SVC 的旧路径。
采用一个简单的历史材料快照：把当前 `harness/skills/svc` 目录链接物化为迁移前的完整 skill，标记其固定来源，只供归档消费者使用。
当前活动 variant 改用五个新目录链接，指向 `sources/svc/skills/<name>`，不会同时注册旧 `svc`。
`scripts/package_hackathon.py` 唯一硬编码的源目录由 `sources/svc` 改到历史 `harness/skills/svc`，保留旧包内路径和行为。
这不维护两套当前 Corpus，也不让归档 variant 无意换上新方法；不新增版本解析器或兼容分支。

## 外部技能材料

`harness/skills/` 新增 HyperFormula、Handsontable、Better Auth 两项与 fixing-accessibility；仍由当前 variant 的 build.py 和 run.py 显式选择。
固定上游 commit、保留适用许可和来源，变更说明写入现有 `harness/dependencies.lock.json` 与 `harness/skills/README.md`。
调查快照的实际下载 ref 与 commit 对应关系保存在 `runs/hackathon-capabilities/research/upstream/*/source.json`，已确认四个快照 ref 等于所查询的 commit。

Handsontable 采用短入口，把长 API 示例和迁移资料放入 references；HyperFormula 同样将完整文档地图作为按需资料。
移动正文时同步修正相对链接；不将旧版本迁移历史预装进新应用的必读内容，也不开发通用文档转换器。
Better Auth 两项保留具体库/插件边界，元数据和正文不要求采用默认邮件、OAuth 或组织权限语义。
当前 better-auth/skills 快照没有声明许可文件；实施采用独立撰写的简短知识入口，依据其 [MIT 官方实现/文档](https://github.com/better-auth/better-auth/blob/main/LICENSE.md)记录事实并链接来源，不复制整份无许可技能正文。
fixing-accessibility 保留具体交互知识，去除默认逐行源码审查的使用界面；实现与观察都以任务需求为准。
这些是知识材料，不向 Harness runtime 预装应用库，不修改现有 npm lock、浏览器、模型或 Braid。

`exploration-tools/assets/mcporter.json` 增加 `handsontable-docs` 的官方 URL。
对应短导航给出 `search_docs` 的 query、limit、ht_version/hf_version 用法；沿用 MCPorter，无额外本地服务。
已从本机直接读取官方 MCP 的 `tools/list`，返回 HTTP 200，确认工具名和四个参数；原始 SSE 见 `runs/hackathon-capabilities/research/handsontable-tools-list.sse`。
库资料或 Context7 足够时不要求调用专用 MCP；官网容器网络能力保留为实验观察项。

## 当前 variant 接线

需要修改的消费者集中在 `variants/pi-team-mixed/build.py`、`run.py:native_files` 和两个成员下的原生角色 Markdown。
主会话注册五个 SVC 技能及获选领域/交互技能，保留 ponytail、impeccable、exploration-tools。
移除两份 instructions.md 中只介绍旧 `svc` 入口的段落；既定工作流程与无人值守说明保持。
原生角色继续 fresh，模型、工具权限及成员分配保持现有配置。
角色的必需方法预装和可选技能元数据分别处理，具体用法以固定版本接口核实为准，不能把所有领域正文预装到每个子角色。

已核实 Pi 0.85.1 与 pi-subagents 0.56.0 都只通过技能配置注入名称、描述和路径，正文不会因此 eager load。
子代理从固定 Pi package 启动自己的 CLI，不继承父 launcher 的 `--skill` 参数；每个角色必须显式列出自己可发现的技能。
保留现有 `inheritProjectContext:false`、`inheritSkills:false`、`defaultContext:fresh`、append system prompt；其中 fresh 是默认选择，显式调用参数依原生接口处理，本轮不改其控制语义。

下表是文件接线，不是 Agent 必须逐个调用的流程；“领域四项”指 HyperFormula、Handsontable、Better Auth 和 organization。

| 会话/角色 | 可发现的 SVC 技能 | 其它可发现材料 | 直接预装的方法 |
| --- | --- | --- | --- |
| 两个成员的主会话 | 五项全部 | 领域四项、fixing-accessibility；原有 ponytail、impeccable、exploration-tools | 既有成员工作约定，不预读整套技能 |
| explorer | investigation、verification、task-packet | 领域四项、exploration-tools | investigation/references/workflow.md，原有探索工具短指引 |
| executor | implementation、investigation、verification、task-packet | 领域四项、fixing-accessibility；原有 ponytail、impeccable、agent-browser、exploration-tools | implementation/references/workflow.md，原有探索/浏览器短指引 |
| specialist | design、investigation、verification | 领域四项、exploration-tools | design/references/workflow.md，原有探索工具短指引 |
| browser-operator | verification | agent-browser、fixing-accessibility | 原有浏览器短指引 |
| vision | 保持原样 | 保持原样 | 保持原样 |

三个 `references/workflow.md` 分别接收当前 Explore、Implementation、Design 的方法正文，`native_files` 的三条来源路径直接改到新位置。
SKILL.md 提供直接可用的要点与进一步资料导航；不把同一方法在 role 源文件和 skill 中各维护一份。
技能元数据与一次方法正文同时存在是有意的；不把元数据误计作第二份正文，也不因迁移删除已批准的角色 SOP。
所有技能物化在同一运行的 `work/skills/<name>`，每个角色使用现有 `skillPath` 解析；没有新的路径协议或路由器。
主会话可以在普通委派里传选中的资料路径；executor 也可以自行选择，不需要经过主会话、explorer 或其它角色批准。

## 实施顺序与分工

1. 主 Agent 保存当前历史 SVC 材料、明确此次源仓与主仓基线及既有未提交改动；提交需用户明确授权，不把开工自动当作提交授权。
2. SVC worker 仅拥有 `sources/svc/skills/` 及源仓维护说明，按上述归属迁移与改稿。
3. 能力材料 worker 并行处理新增外部技能及来源说明；不改 variant、SVC 或冻结资源。
4. 主 Agent 在材料就绪后完成五目录链接、主/子会话加载接线、历史 packager 源路径及相关 CONTRIBUTING/技能说明。
5. 从当前 Linux runtime 重新装配新包，不重装依赖；保留原实验 ZIP、submission、journal。
6. 根据届时已授权实验矩阵完成官网真实运行；完整结果一次汇报。

一次集成中使新入口、正文与消费者一致，不建立临时兼容装配层。
子任务遇到范围、素材许可或原生 API 不支持等真实阻断时，带证据返回主 Agent；局部路径与文案调整由负责人解决。

## 验收与具体影响

沿用 design.md 的真实实验判据：GitHub、Sheet 各有完整评分和过程证据；区分交付失败与有效低分，观察选读、采用、反馈与额外成本。
实施中以编辑复核、原生接口资料和真实打包产物核对材料；不编写或运行 Factory/Corpus 测试，不将测试改名成探针。
本轮不会改正在运行的制品，也不会自动开下一轮实验；新包提交与比赛运行在开工复核中明确授权范围。
尚未验证的官网出网、技能是否被 Agent 实际采用，只能由后续真实轨迹回答。

## 预演后的收敛

已解决的准备问题是：原生元数据加载行为、子会话不继承 launcher、显式角色技能列表、SOP 的唯一来源、旧 SVC 消费者与分发相对路径。
预演中“主会话先选技能再派发”仅保留为一个使用例子，不增加强制协作顺序或委派字段。
未创建的新目录属于待实施内容；未观察的模型采用和官网出网属于真实实验问题，均不伪装成已经验收。
