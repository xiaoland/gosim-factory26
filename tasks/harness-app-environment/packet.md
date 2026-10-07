# Harness 应用开发与评测环境统一

## 目标与授权

让参赛 Agent 的应用安装、开发、Vitest、构建、reviewer 启动和独立评测使用一致的 Node 与 npm 环境，减少原生依赖 ABI 错配、依赖目录混用和临时修环境的成本。环境应由 Harness 默认提供，不依赖 Agent 记住 app-env、临时调整 PATH 或开发人员介入运行。

2026-10-07 用户认可“应用开发、Vitest、构建、reviewer 启动和重放统一使用官网 Node 20.19.3；Pi、portless 等需要 Node 24 的工具通过绝对路径使用自己的 Node，子进程继续继承应用环境”，并补充：“结合 pnpm 的问题，我认为可以进一步统一到 npm，尽可能避免开发和 Eval 阶段的环境差异以及额外的环境处理负担。这是一个新的任务，建立 task packet.”

最初授权仅建立任务包和记录方向。2026-10-07 用户进一步明确：“你可以开始，这也是基础设施改进的一部分”。当前已授权实施公共启动环境、工具启动器、两个DX variant及实际评测入口的统一，纳入决赛设施改进；不扩大到I15或历史variant，不热改在途运行。真实Linux应用安装、Vitest、构建、服务启动与独立副本验收用于反馈，原设施真实模型矩阵与绝不参赛的边界不变。

主负责公共安装器/工具启动器、两个DX入口、指令及文档；execution_owner负责Linux部署和真实应用操作，处理其局部故障并将必要源码修复协调给主。新增独立执行owner被平台thread limit拒绝后采用此分工，不用另建聊天绕过限制。两者共享代码库，保留其它任务的改动。先完成默认环境与工具解释器分离，再接入DX并操作已有真实应用独立副本；最后由正常启动/接续消费新版本，不为环境更新中断活跃运行。

## 已决定的方向

- 应用默认使用官网 Node 20.19.3 和 npm，覆盖普通实施者、reviewer、原生子角色、服务启动及接续入口；记录并对齐 npm 版本与安装策略。Node 版本依据当前平台交付合同，不能成为脱离平台条件的永久常量。
- Harness 工具保留各自必需的运行环境，通过明确可执行路径启动。工具自身使用 Node 24 不应把应用子进程切换到 Node 24；须核对 portless、bash 和子角色的实际环境继承。
- 用同一应用包管理器减少开发与官网验收差异，移除活动范围内要求 pnpm 的指令及接线；已有 pnpm 锁文件、npm 锁文件和基线的迁移规则需要核实，保留应用与业务数据。
- 隔离验收副本、数据库、缓存、上传目录和进程，不能因 Node/npm 一致就共用开发工作树中的可变状态。不得让隐藏评测反馈回流生成。
- 对齐有实际影响的系统与架构、原生编译条件、安装生命周期策略、HOST/PORT、目录和正式构建/启动路径；不追求抹平工具内部无关差异，不建立通用环境管理或恢复框架。

## 已有证据与未决问题

I14 GLM-root 完整 GitHub run 为 `20261006-125849-7a406ace`。PR8 原生记录显示，10月7日 08:34（北京时间）删除 node_modules 并前置 `/usr/local/bin` 执行 pnpm install 后，模块仍是 ABI 137，而 Node 20 测试要求 ABI 115。08:35 Agent 因怀疑 pnpm 的 Node 接线而改用 npm rebuild；15:12 接续时普通命令使用 Node 24，又遇到 ABI 115 模块与 ABI 137 执行环境不符。不能把它仅归因于 Harness 注入旧应用依赖。

该运行的实际 pnpm 启动器为 `exec "${FACTORY26_APP_NODE:-$HERE/node}" .../pnpm.cjs`；只改 PATH 不改变默认工具 Node。现成 app-env 会设置 FACTORY26_APP_NODE，但 Agent 未采用。更早 PR2、PR5 在开发工作树原地执行官网 npm 安装，Agent 已意识到可能改变 pnpm 依赖布局，仍选择原地操作和后续恢复。这里既有环境接线问题，也有验收边界消费问题。

当前源码的公共安装器安装 Node 24.10.0；DX 与 I15 入口把工具 runtime/bin 放在 PATH 首位。公共 npm 清单未声明 pnpm，但部分活动指令仍要求 pnpm；安装器可跳过不存在的命令后写成功标记。较早 Linux 安装现场包含 pnpm，采用不同清单与安装器版本，只证明该版本工具依赖安装成功，不能作为当前精简版本应用环境正确的证据。

Vitest 全套曾被 300 秒总时限终止，分批随后 96/96 通过。组织/仓库批次前五条各耗时 29–51 秒，后八条约 1.6–1.7 秒；源码重复执行完整种子并使用同步 scrypt，尚无函数级计时解释异常波动。Node/npm 统一不能预先宣称已解决全部慢点；分批跑和单纯延长超时不作为本任务根治标准。

证据入口：

- [原运行及恢复记录](../iteration14/glm53-root-full-github-20261006/packet.md)。远端原生会话位于 `sfp7-ws.localhost:/home/yyh/factory26-manual-glm53-full-github-20261006/output/.factory26/20261006-125849-7a406ace/work/native-homes/`，重点为 `pi-glm-fast-01a113b9-*` 的原 PR8 与 `pi-glm-fast-01a11532-*` 的恢复会话；本次侧会话只读取证，未回收原件。
- [安装器](../../submission/runtime_install.py)、[公共依赖清单](../../harness/npm/public-package/package.json)、[旧构建入口](../../submission/build.py)、[平台交付合同](../../harness/skills/arc-bench/references/platform-delivery.md)。源码正由其它任务演进，实施前重新核对实际版本。
- [较早 Linux 安装证据](../../runs/public-package-linux-AodKRb/linux-installer-evidence.txt)，对应远端 `/home/yyh/factory26-lab-runs/public-install-20261007-132759`；该现场不是当前源码的安装验收。

## 后续工作与完成标准

2026-10-07 主会话已核对当前两个DX入口：Pi的默认PATH前置runtime/bin，并全局设置NODE_PATH到工具依赖；I14同样前置工具路径、指令仍要求pnpm，而公共清单没有pnpm。browser_runtime已有工具Node绝对路径的启动方式，可以复用。advisor判断：本地与官网使用相同安装入口并不证明应用环境符合平台；应用默认Node/npm归公共执行环境，工具解释器归各启动器，应用依赖及迁移归应用交付合同。此问题不作为当前proxy 502或I14 blocked的既定根因。

实施范围限于公共启动环境、实际需要Node24的工具启动器、两个DX的环境/指令及评测入口，不默认扩大到I15或历史variant。普通应用子进程使用平台Node/npm，工具内部组件仍可使用工具Node；工具依赖不通过全局NODE_PATH泄漏给应用。新应用直接使用npm，已有应用在独立副本中核对锁文件与逐目录安装；跨ABI的node_modules重新安装，保留源码与业务数据。

先确定活动范围并逐一追踪公共安装器、包入口、variant 环境、原生工具、子角色、服务启动、恢复及评测的实际 Node/npm 选择；核对平台 Node/npm、操作系统、架构及编译条件。形成具体改动范围与基线迁移规则，再按授权实施，复用现有入口而非新增一套框架。

完成须以真实 Linux 应用操作证明：从无预装业务依赖的环境启动，普通 Agent 命令和 reviewer/子角色/portless 启动均使用目标应用 Node/npm；含原生 SQLite 依赖的应用能完成安装、Vitest、构建、正式启动及独立验收，全程无需临时 app-env/PATH 补救或切换包管理器。安装失败保留具体错误与真实退出码，不能以 marker 或工具安装成功替代此证据。热缓存和接续的原生依赖不得跨 ABI 误用；平台 npm 交付路径和已有业务数据仍有效。

遵守项目规定，不新增或运行 Factory/Braid 测试或包 smoke；使用编译、真实操作及明确授权的应用验收/实验取证，付费模型运行另行明确范围。持续知识最终更新现有技术、运行说明和 Agent 环境指引，packet 仅持有本任务状态。

当前状态为已授权实施，尚未取得新环境的实际验收结果。此packet继续持有应用环境问题的证据与实施状态，决赛设施packet只链接本范围，不复制环境合同；不新增配套模板。

当前源码已提供runtime_install.application_environment：默认PATH使用平台/usr/local/bin和不含node的runtime/tools，移除全局NODE_PATH；工具启动器显式调用runtime/bin/node或原生入口。两个DX已消费该接口，I14不再要求pnpm；Pi原生接续保留原始指令，只替换当前有效环境段，并按producer保存实际指令。Python语法解析和diff检查通过，尚未部署资格化。execution_owner使用公开GitHub官方基线的独立副本开展真实npm安装、应用Vitest、构建、正式启动与portless/后台bash操作；不控制旧610daf或活跃Pi，不读取隐藏评测器。其它会话已有的Tailwind及完整用户旅程指令改动保留，不纳入本次环境提交。
