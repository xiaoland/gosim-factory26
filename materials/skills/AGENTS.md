# Agent Skill 编写与维护

本文件指导开发 Agent 维护本目录的技能材料，不是参赛 Agent 的技能正文。根 AGENTS.md 的授权、实验与知识归属规则继续适用。技能来源、许可与适配记录归 [README.md](README.md)，实际启用和分发归各 variant；先核对消费者，再修改材料。

## 遵守格式与加载合同

以 [Agent Skills 官方规范](https://agentskills.io/specification) 为格式依据。每个技能目录至少包含 SKILL.md，文件由 YAML frontmatter 和 Markdown 正文组成。name 必须与目录名一致，长度为 1–64，只用小写字母、数字和连字符，首尾无连字符且无连续连字符；description 为非空的 1–1024 字符，说明技能做什么、何时取用。可选字段只在有实际需要时添加，遵守其类型与约束。

发现入口只提供名称、description 和路径；完整正文在选用后读取，references、assets、scripts 按需取得。技能正文和附属正文始终保留为独立文件，不内联进 system、profile、role 或 task prompt。使用相对文件链接，常用分支从 SKILL.md 直接可达，避免逐层追链接才能找到必要依据。脚本说明真实依赖、输入输出与失败行为；上游许可随材料保留。

客户端专属字段与行为先核对本项目实际加载器。matt-skills 的用户调用、模型调用及 router 区分可帮助判断发现成本，但其中 disable-model-invocation 等机制不是本仓库自动具备的能力；不要据此删掉必需的 description 或假设新增字段已经生效。[来源：Skill Mechanics](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md)

## 让入口可靠触发

description 和 reference 指针是读取条件，不是内容目录。用实际任务语言表达能力与不同触发情形；同义词不重复列成多个分支。链接附近说明遇到什么问题应读、读取后支持哪个判断。必要材料未被取用时，先核对指针措辞与实际发现面，不用复制正文解决触发问题。[来源：Writing for Agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)

## 按使用分支组织内容

SKILL.md 保留各次取用共同需要的核心判断和入口；只服务某些分支的命令、字段、长例子、环境差异及排障细节放入相应 reference。每次增加内容先找已有归属并改写整合，不默认追加章节。reference 围绕一个完整问题组织，使读者取得足够依据采取行动；概念的定义、规则和例外就近放置。

拆分依据是材料何时需要，以及独立触发是否有价值，不是固定字数或一条规则一个文件。官方建议 SKILL.md 少于 500 行、正文少于约 5000 tokens，这些是上限提示，不是填充目标。主文件既要克制，也要足以完成常见判断，不能退化为一串无读取条件的链接。步骤型、原则型和混合型都可以成立。[官方规范](https://agentskills.io/specification)、[信息层级方法](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)

## 原则要能改变决定

原则型、why/what 型技能受到鼓励。对会影响行动的概念，给出必要定义、适用条件、因果理由与边界，使 Agent 能区分何时采用、何时调整。用少量有辨别力的例子或反例澄清易混淆之处；“充分理解”“合理拆分”等词不能独自承担判断依据。matt 的 [Codebase Design](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) 可学习之处是概念、关系和可判断问题相互支撑，具体术语和架构主张不直接移植。

有顺序的动作写明可判断的完成条件；原则型正文也要让使用者辨认结果是否成立。优先表达目标行为，必要硬边界注明作用范围，避免将局部禁令泛化到整个任务。概念用词保持一致，不靠自创缩写或关键词堆积压缩含义。

## 保持归属，核对实际采用

共同方法保持一个权威来源，通过明确指针复用。项目政策、某个配方的角色限制、单次任务参数与通用方法分别归其实际 owner；更新技能时不要把近期事故、具体赛题答案或历史报告逐条沉积进去。命令字段和配置事实优先从 CLI help、源码及配置取得，技能只保留采取行动所需的用法与非显然边界。借鉴上游时保留有用的判断模式，逐项核对其审批、工具、测试和交付流程是否符合本项目授权与运行合同。

交付前人工核对 frontmatter、文件链接、读取条件、内容归属及实际工具能力。需要行为证据时，在已授权操作或实验中分别观察发现、读取、采用和结果；文件存在、读取成功或文本变短不证明技能有效。工具校验复用已有能力，并遵守本项目实验与测试边界，不为技能内容建立测试或将测试改名为校验脚本。本文件本身也按这些原则维护，保留能改变写作判断的指引。
