# 原生接线与工具取得方案

本页是已通过复核的技术设计，尚未实施；具体实施计划见 plan.md。
保持原生 Codex/Pi 子 Agent，不改变 Braid 调度，不加入父历史过滤代理或新的角色框架。

## 角色内容与分发

Hackathon 的 `submission/hackathon_main.py:write_roles` 继续写原生 TOML/Markdown。
将供主会话选角的 description 与子角色正文分离；较长的正文放在 `submission/agents/<role>.md`，模型仍在现有明确映射中。
打包器显式收集这些文件，不引入一个新的全局 preset/config 生成层。
Braid 的原生角色文件继续由各 variant 独立维护，不改成 import Hackathon 角色或共同生成 variant。
工具材料作为 skill 复用，与现有 agent-browser 分发方式一致。

SVC 组按角色从已安装 skill 的指定文档读取原文，附文档绝对路径和所在目录再装入角色正文；相对引用以该来源目录解析。
这读取的是随制品冻结的文件，不在执行中下载最新版，也不把完整 Corpus 预读到所有角色。
base 组不读取或引用这些 SVC 方法文件。
方法原文与工具知识不复制到 description；生成的原生配置仍作为实际上下文证据保留。
SVC skill 的规范目录与现有入口不变；本轮不改 Corpus 正文。

## 上下文配置

Pi 四角色明确 `defaultContext:fresh`、`inheritProjectContext:false`、`inheritSkills:false`、`systemPromptMode:append`，显式选择角色所需 skills/skillPath。
父调用明确 `context:fresh`，覆盖调用层的歧义；`settings.json` 设置 `subagents.disableBuiltins:true`。
append 保留 Pi 原生工具的基础使用方法，不是继承父会话 transcript。
Braid 五角色已有这些字段，修改其父委派指令中“默认不复制”的软描述为明确独立历史策略。
Pi 模型 descriptor、主模型与供应商推理参数保持本轮现状；角色缺省 thinking 的改变不混入这次方法实验。

Codex 继续用 `CODEX_HOME/agents/*.toml`，保留各角色 model 和 model_reasoning_effort。
父指令按工具公开字段显式使用 V1 fork_context:false 或 V2 fork_turns:"none"；不添加未支持的角色 TOML 字段假装强制历史隔离。
两套参数已由 rust-v0.155.0 的 `multi_agents_spec.rs` 核实；实际采用哪套及传值由原生记录确认。
Codex 角色仍使用原生工具；只读职责由角色授权约束，不新建沙箱层。
角色所选详细技能正文/入口写入其 developer_instructions，避免“home 中发现了 skill”等于“子 Agent 已拿到相关知识”的误判。
现有 home 的全局技能目录不当作逐角色排他工具权限；本轮目标是角色获取必要知识，而非访问控制。

## 探索工具

| 能力 | 取得方式 | 角色使用方式 |
| --- | --- | --- |
| rg | Linux 构建阶段安装 ripgrep；按现有工具二进制及动态库拷贝方式装入 runtime/bin。 | 字面量/文件定位；Pi 原生 grep/find 仍可直接用。 |
| ast-grep | 锁定 npm `@ast-grep/cli@0.45.3`，与现有 npm lock 一起构建。 | 用完整命令名 ast-grep，避免 sg 同名冲突；结构问题再读取该语言的 pattern/rule 帮助。 |
| Context7/Exa | 锁定 `mcporter@0.14.0`，通过其现成 CLI 调用远端 MCP。 | 按已知工具调用；遇到参数问题时定向 list 该工具 schema，不先读取全部工具。 |

两个 npm 版本由 2026-09-24 registry 元数据查得；MCPorter 要求 Node>=24，当前运行资源为 Node 24.10.0。
独立预演已在 WSL scratch 安装两包，并使用运行资源的 Node 24 完成 MCPorter 的 Context7/Exa 真实查询；ast-grep 也在实际仓库源码上完成结构搜索。
安装时使用宿主 Node22/npm，运行时明确用 Node24；最终 Docker Node24 的 npm ci 与制品布局仍待实际构建，不能用 scratch 结果替代。
ast-grep 的入口是原生 ELF，必须直接 exec，不能加入现有统一用 node 启动 JS CLI 的循环；mcporter 则使用现有 Node wrapper 方式。
不使用执行阶段 npx 临时安装，也不编写自有 MCP client/daemon。

配置通过原生 `MCPORTER_CONFIG` 指定唯一文件，设置 imports:[]，只列 context7 与 exa 两个服务。
这使实验接入由制品定义，不取决于宿主编辑器的服务配置；不是新增沙箱。
服务地址为 `https://mcp.context7.com/mcp` 与 `https://mcp.exa.ai/mcp`。
调用保持 `--no-oauth`，无人值守任务不进入交互登录。
文档提供公开接入，2026-09-24 不带凭据 tools/list 两者均返回定义；随后独立预演完成 Context7 库定位/文档查询和 Exa 搜索/取页，见 rehearsal-tools.md。
这证明当次请求可用，不保证后续查询额度与网络状态。
认证、限流和具体请求错误如实返回给 Agent，由当前信息需要决定替代来源或报告缺口，不静默宣称已有结果。

当前工具定义已保存到 `runs/factory-subagents-research/{context7,exa}-tools.txt`：

| 服务工具 | 已观察的必填参数 | 用途 |
| --- | --- | --- |
| context7.resolve-library-id | query、libraryName | 从库名/需求定位正确库及版本候选。 |
| context7.query-docs | libraryId、query | 针对一个具体 API/行为问题读取文档。 |
| exa.web_search_exa | query、objective | 说明想找到什么资料及判别目标。 |
| exa.web_fetch_exa | urls | 读取已定位来源，可批量。 |

示例形态为 `mcporter call context7.resolve-library-id --args '<JSON>' --no-oauth`。
复杂 shell 参数使用 JSON 对象，角色无需记住全部可选参数；以实际 schema 为准。
工具选择材料以这些真实接口编写，避免沿用网络文章里的旧 Exa 参数。
不将外部检索扩展为查找 benchmark 测试、参考实现或历史答案；Factory 已有的公开需求输入边界仍适用。

## 具体影响与准备事项

源码范围为 Hackathon 角色装配与主指令、对应包材料、runtime 的工具取得、Braid 各角色/主指令，以及受影响的操作说明。
模型、Braid 生命周期、SVC Corpus、官方 Runner、已冻结 ZIP 与旧运行均不改动。
新工具和指令对 base/SVC 两组同时生效；SVC 差异是方法材料及其装载方式。
这与旧冻结包存在多个改变，不能用旧新单次得分差直接归因给某一种工具或 SOP。

实施准备已得到 CLI 和真实文档查询证据；原生上下文配置及观察路径见已完成的 rehearsal-context.md。
目标 Docker 构建尚未发生，准备结果不替代开工确认或真实模型验收。

接口来源：MCPorter [README](https://github.com/openclaw/mcporter)、[CLI](https://github.com/openclaw/mcporter/blob/main/docs/cli-reference.md)、[配置](https://github.com/openclaw/mcporter/blob/main/docs/config.md)；Pi 锁定包的 agents/configuration 文档；Codex 固定版本源码见 findings.md。
