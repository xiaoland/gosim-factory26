# pi-minimal 验收方法接线

2026-09-30，状态：源码接线完成，真实模型采用与应用验收尚未验证。用户授权继续迭代 pi-minimal，加入 SVC V&V Agent Skill 或成熟验收方法；本支线只修改 variants/pi-minimal 与本记录，不启动模型、实验或官网提交。主线仍为 I12，本次不覆盖 pi-minimal 的已有运行和主 packet。

## 问题与取舍

pi-minimal 原生入口实际为 main.py，没有 run.py。原指令已经要求从需求设计验收、用 agent-browser 获取开发反馈、最终执行完整可重复检查，但没有向主会话或 advisor 提供对应的方法材料。build.py 还会从 agent-browser 的打包副本删掉 svc-verification 的结果解释引用，因此浏览器执行记录与验收结论之间没有完整方法接线。

采用现有完整 svc-verification，不引入其它 SVC 技能、CLI、任务体系、Braid 或新角色。其入口及四份 references 覆盖需求到判据的转换、检查条件和观察边界、可重复执行、结果解释与候选变化后的适用性判断。所有 Markdown 链接均在这五份材料内部；两处文字提及 design skill，不是命令或资源硬依赖。主会话与 advisor 的自然说明将其对应到既有产品和技术设计步骤，避免无声引入 svc-design，也避免让从未见过 SVC 的模型理解整套体系才能工作。

agent-browser 保持真实页面探索与快速反馈用途。完整验收由主会话依应用需求编写可重复自动化测试或脚本，通过真实 UI 路径观察承诺的状态变化，组件/API 检查与截图支持各自范围的结论。已有 agent-browser/scripts/with-service.py 可以保存完整输出、实际退出码与所验候选并清理拥有的服务；复用该技能内工具，无需新建 browser-checks、浏览器验收角色或预制应用检查源码。方法不绑定具体 benchmark、评测器或评分细节。

## 实际改动

main.py 和 build.py 的显式技能选择加入 svc-verification，其余七项维持原有选择。build.py 复用 copy_skill，从 harness/skills/svc-verification 物化 SKILL.md 与完整 references；该目录链接到 sources/svc/skills/svc-verification。移除对 agent-browser 正文中结果解释引用的删除。主会话增加 --no-skills，关闭默认技能发现，逐项 --skill 加载所选材料。

advisor 的 skills 声明加入 svc-verification，继续使用独立 skillPath、inheritSkills:false 和 fresh 上下文。其职责仍为只读建议，主会话负责实际执行和最终交付；advisor 的同意不替代证据。

instructions.md 介绍该方法的能力与读取时机，要求按问题选择相关 references，并说明失败、初始状态、条件等待、服务清理、原始输出、退出码及代码变化后的结果适用性。README 更新当前能力边界，避免“无 SVC”被误读成没有采用独立来源技能。vendor/ponytail、其它 variant、SVC 源码、全局支持、凭据与旧 run 均未修改。
主线整合时将两份角色索引收敛为自然的方法介绍，去掉重复讲述SVC系统划分及正文里已有的验收要求；详细步骤仍以技能及其references为准。

## 已获得的证据与限制

Python AST 解析 main.py、build.py 成功；静态解析显示两处技能选择一致，八项入口均存在，svc-verification 全部相对 Markdown 文件链接可以解析，agent-browser/scripts/with-service.py 存在。git diff --check 无错误。以上只建立语法和材料路径事实，不构成模型采用或生成应用验收。

核对已有 native-fix runtime 中的原生 Pi 文档与 dist/core/resource-loader.js，--no-skills 关闭默认发现时仍合入 CLI 显式技能。核对 pi-subagents/src/api/preflight.ts 与 src/agents/skills.ts，角色以 skills/skillPath 解析材料，并在系统提示中提供名称、description 与文件位置；正文及相对引用按需要读取。svc-verification 入口的 name、description 非空，名称与目录一致，不依赖第二份自建索引。

材料采用来源当前工作树，SKILL.md metadata.version 为 16.0.0。sources/svc 的 HEAD 为 0cf1406fa9b3bdd0911c5873bcbf69a976db3a5b；本次读取时入口、interpreting-results.md、repeatable-checks.md 有既存本地修改。因此只取得该 HEAD 不能复现本次材料，后续冻结包应保留实际材料内容与制品身份。本次未改动这些来源文件。

没有运行 Factory、SVC、Braid 或基础设施测试，也没有包 smoke。本次未重建 runtime、未冻结上传 ZIP、未调用模型、未运行生成应用或官网评测。下次独立获授权实验应重新装配 Harness，并从原生会话确认主会话与 advisor 实际读取相关技能，以及应用脚本的原始输出、退出码和需求覆盖；仅看到材料装入目录或系统提示不能声称方法已被采用。旧冻结制品与在跑实验不会因此自动更新。

建议主 packet 只链接本记录，保留已有运行身份与授权历史；本次没有提交 Git。
