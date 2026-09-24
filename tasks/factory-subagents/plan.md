# 实施准备与开工影响

设计、技术与验收方案已获用户认可，原话为“很好，这个方案没问题。”。
两项独立预演已完成。用户已授权开工，并明确本轮不进行验收，几轮迭代后再统一实验。

## 独立预演

| 负责者 | 独占范围 | 返回物 |
| --- | --- | --- |
| subagent_context_rehearsal | 原生 Pi/Codex 角色、历史继承、SVC 材料装载与已有观察路径 | rehearsal-context.md |
| subagent_tools_rehearsal | WSL 独占临时目录的 CLI 取得、工具帮助及当前任务相关的真实文档查询 | rehearsal-tools.md |
| 主 Agent | 文件责任、依赖顺序、实验可执行条件、结果整合与开工说明 | 本页及 packet |

预演不修改运行源码、共享 runtime 或冻结包，不启动模型/benchmark，不编写或运行基础设施测试。
临时工具安装属于独占运行材料；原始查询结果保存在 runs/factory-subagents-preparation，不转化为测试框架。

工具预演已完成，详见 [实际结果](rehearsal-tools.md)：WSL scratch 中的 ast-grep 0.45.3 能搜索实际源码，MCPorter 0.14.0 在 Node24 下完成 Context7/Exa 真实文档请求。
实施时 ast-grep 直接 exec 原生 ELF，mcporter 通过 Node24 启动，避免照搬同一 Node wrapper。
宿主已有 rg 不等于制品包含 rg；目标 Docker 的 npm ci、二进制与依赖拷贝仍须随实际构建确认。

上下文预演已完成，详见 [原生接线结果](rehearsal-context.md)。
Pi 同时明确角色 fresh 默认值、父调用 context 和内建角色关闭；Codex 保留原生 agents 目录发现，父指令按实际工具协议选择无历史参数。
SVC 完整 skill 现已可用，选定章节直接装入角色正文，不改成读取提示，也不新增上下文代理或遥测设施。
配置和原始会话分别作为证据；归档缺少有效 system prompt 时保留该缺口。

## 实施顺序与责任

1. 设计基线已提交为 a6d5276，仅收录本 packet。
2. 工具材料与 Hackathon 角色装配可以并行完成，两个执行者拥有不同文件。
3. 主 Agent 将已就绪材料接入四个独立 Braid variant，整合运行资源与操作说明。
4. 整合源码与操作文档，记录本轮实现结果和待验收事项；本轮不构建验收制品、不启动模型或 Runner。

| 实现责任 | 拥有的文件 | 明确变化 |
| --- | --- | --- |
| 工具与知识材料 | harness/npm/package.json、package-lock.json；submission/Dockerfile、build.py；harness/skills/exploration-tools/ | 冻结 rg、ast-grep、MCPorter；提供实际工具选择与调用指引，沿用现有运行资源机制。 |
| Hackathon 角色装配 | submission/hackathon_main.py、submission/agents/；scripts/package_hackathon.py | 分离 description/正文；选定技能与 SVC 章节；fresh/无历史；关闭 Pi 内建角色；移除固定流水线；打包实际材料。 |
| 主 Agent 整合 Braid variants | 四个 variants/pi-team-*/run.py、build.py、六套成员 instructions.md 及相应 agents/*.md | 每个 variant 独立声明/装配技能与方法；specialist 去掉失败前置；父调用明确 fresh。 |
| 主 Agent 文档与验收 | CONTRIBUTING、受影响 Deployment、当前 packet | 写清使用与证据路径；不增设新的角色配置框架。 |

Braid 的 vision 保持纯图片职责；browser-operator 的原生会话方式沿用最新已提交修正，不恢复被删除的 browser.py 包装层。
单个浏览器任务使用默认会话，并行任务才用不同命名会话；会话归任务，不绑定 Agent 身份。
role Markdown/model/settings 保持原生语义，不让脚本解析出另一层 preset。
工具配置与 skill 安装路径由运行入口写入当前运行材料；新增的实际工具能力对同一对照的 base/SVC 两组一致。
Hackathon role 字符串只在既有 native writer 做必要格式输出；Braid 各 variant 独立演化，不 import Hackathon 生成器。

## 必须保持的当前行为

主模型、子模型和供应商推理/输出长度策略不变。
SVC Corpus 正文和标准 skill 分发目录不变；只改变角色如何取得已存在的对应方法。
Braid 核心、生命周期、交付选择、Runner、已在运行或排队的实验及历史 ZIP 不变。
不新增沙箱、验证中间层、MCP 协议实现、可配置角色引擎或 Factory/Corpus 测试。

## 后续统一实验的候选安排（本轮不执行）

2026-09-24 WSL 只读确认：platform-inputs/hackathon/github、sheet 下只有 requirements/ 与 source.json，没有官方 tests/。
四个新配置在这些输入上能做生成与部署验收，但不能得到官方分数；不将 requirements-only 当完整 bench。

后续可在官方本地 Runner 上执行四配置 × ARC-Bench-Lite 两题（Keep、BookStack），共八个 task run，也就是四个完整 variant bench。
沿用自购模型网关及当前供应商默认参数，最多四并发；不重新安装 Runner/浏览器，不改变当前 Hackathon 控制器。
用新生成的独立 manifest/运行目录保存本轮，生成阶段仅输入公开需求，冻结应用后进入官方测试评分。
这给角色改造提供完整评分反馈，不代表 Hackathon 两题已完成计分验收。

Braid 四 variant 的源码同步落地且可打包，不自动再扩成四个 Braid bench 矩阵；需要运行的 Braid 对照单独由下一轮方向确定。
用户明确本轮不实验；这一矩阵仅留作后续候选，尚未获得运行授权。
每个 run 由一个分析 Agent 独立分析，主 Agent 综合；完整 variant 成绩先报告，不滚动扩展新实验。

## 完成与剩余限制

本轮完成范围为源码、依赖声明与必要操作说明。目标构建、实际上下文生效和评分尚待后续统一验收，不宣称已通过。
原生工具配置与实际接收上下文须分别呈现，不能将 fresh 指令冒充运行时硬限制。
没有在任务中自然使用的角色/工具记为未观察，不额外编排无收益流水线来补满调用表。
若公开 MCP 服务认证、额度或网络阻断，保留具体错误并判断当前任务是否仍可完成；不静默换模型或宣称查询成功。
