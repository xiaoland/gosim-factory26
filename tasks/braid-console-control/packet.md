# Factory26 Exp Console

2026-10-02 当前接续：[当前实验接入修复](current-runs.md)。8765 已切换为 Mac 原生只读 Console，正确接入两组当前 baseline；旧 Debian-Rebuild 服务保留为历史入口。以下 2026-10-01 部署身份与验收均为历史记录。

2026-10-01。独立实验基础设施任务。彼时唯一服务为Debian-Rebuild上的原生Python Console，Mac8765只作SSH转发。用户已删除原Debian-Factory26，并取消六条Console登记与journal迁移，采用空登记基线；历史部署身份只作下面的证据，不再当作当前状态。Console不属于I13或生成Harness迭代。

## 当前恢复点：阅读能力已部署，两条新现场已验收

用户先要求用树整理外部变化，随后明确“是的，没错，按这个推进”。本轮已完成整理后的清理、空基线部署、精确接入、真实验收与本任务限定提交；不push。

```text
Exp Console
├─ 产品范围［完成］
│  ├─ Provider默认对话，工具/思考折叠，错误直接可见
│  ├─ 同源Trace、完整原始记录、调用/结果分别定位、返回阅读位置
│  ├─ Agent/Provider登记工作区文件，Markdown源码与预览
│  └─ run级origin各分支，固定完整commit只读阅读
├─ 验收［完成本轮真实Pi范围］
│  ├─ TypeScript/Vite、Python编译通过；未运行设施测试
│  ├─ 空基线及两条新现场HTTP、浏览器深链/刷新/前后导航
│  ├─ 跨页工具配对、真实错误、Chat/Trace位置、文件/分支位置保留
│  └─ 390px对话及文件布局实际核对，最终浏览器无warning/error
├─ 唯一部署［已上线］
│  ├─ Debian-Rebuild，Python3.13.5，原生HTTP PID163346
│  ├─ service 4161a417-fede-4be5-b692-162350a3d826
│  ├─ /home/yyh/.local/share/factory26/exp-console/20261001-session-reading-release
│  └─ Mac8765独立SSH转发PID93554；服务和转发均无自动重启
├─ 新运行接入［完成］
│  ├─ I13-GLM/GitHub：glm-root--hackathon--github-f9e238c1b698a5
│  ├─ I13-GLM/Sheet：glm-root--hackathon--sheet-a45a22ec644204
│  └─ 每项独立CLI访问容器，共享原named volume及official-generation子目录
└─ 旧迁移［已取消、临时材料已清理］
   ├─ 不恢复原发行版，不导入旧六条记录或journal
   ├─ 移除迁移特有的code.json归档映射，保留live代码读取范围
   └─ 已停止VHD复制并删除本任务临时副本及未执行的迁移脚本
```

用户开工原话：“同意，你可以开始了。你可以自由提交，也可以随意重新部署现在的那个实例。”后续位置修正：“直接在 Debian-Rebuild 就行”。基线决定：“不必在乎 console 运行记录了，运行包很早就导出了，我们可以有一个干净的基线，重头开始”，并告知正在重启`I13-GLM/*`两项。这覆盖此前保留原六条登记与journal的迁移安排；取消的计划及下方部署身份只作历史来源。

新现场来自`runs/iteration13/local-rebuild-20261001/experiment`的manifest `exp-20261001-184401-7c84dd`、operation `4718c005aa48a8b7d328c007`及真实resource/transport。实际request保留GitHub namespace `20261001-074336-af6f78cd`，Sheet为`20261001-104900-3b994a70`；没有按新lab run名猜namespace。生成期间Mac阶段目录不更新，不能作为live来源。producer run.json原字节复制到稳定服务sources，缺失的实验名和终态保持未知。

Docker的Mounts.Source只给volume根，HostConfig中的Subpath决定实际文件根。Console用户不能遍历Docker宿主数据目录，故共享挂载按同volume/目标的Subpath核实，state/workspace存在性在已验证所有权和挂载的访问容器内检查；准确宿主映射供GC引用，稳定binary哈希仍在宿主核对。本机接入保留原目录检查。没有升root、chmod或修改lab transport。访问容器使用`--init`、无网络、不启动Agent。部署只替换Console自有访问容器；两条原runtime完整ID与StartedAt保持，最终均Running且未Paused，没有业务提交、pause/resume或模型启动。

最终冻结12个程序及前端文件，与本地release-files逐项一致。旧HTTP PID75042已退出，旧manifest退役，旧配置、active、launch和journal保存到新根history；此前空基线及中间版本只作本轮历史。最新身份与原始回执归`runs/braid-console-control/20261001-session-reading-implementation/release-deployment.json`、`release-identity.json`、`release-http.json`及页面截图。完成范围与未观测边界归[Agent Session阅读记录](provider-session-reading.md)，通用操作归[Console README](../../consoles/README.md)。

访问容器使用同一named volume，形成Docker实际消费者引用，防止实验结束时材料被清理。lab清理遇到volume仍被占用会保留具体错误并记未确认，不改变生成或评分结果。最终清理必须先关闭转发和HTTP、停止访问容器、release接入、明确移除该访问容器，再执行实验资源清理；仅停止容器仍保留volume引用。原runtime被移除后，Console读取与物理控制分别判断，不声称仍可控制原生成。

取材期间创建的Windows临时VHD复制已在核对PID23360完整Copy-Item命令后停止；核对独有临时文件为普通文件、长度45,925,531,648字节后删除。它不再是恢复来源。Rebuild未执行的迁移脚本及本地同用途材料也已删除，没有对原实验数据做转换。原六条记录、旧journal或旧磁盘不属于本轮完成条件。

## 2026-10-01：位置调整后的迁移尝试（已取消）

用户在部署时明确“我不认识 Debian-Factory26，如果是容器的话，那就太过度了，完全没必要这样套壳，直接在 Debian-Rebuild 就行”。已解释前者是独立WSL发行版，非Console容器；按指示改为Debian-Rebuild原生HTTP，不创建Console容器或恢复生成。Rebuild有Python3.13.5/Git2.47.3，原服务、四workspace及Docker接入均不在其中。经advisor核对，保留六个run IDs，两archive原样迁移，四个已停止现场转换有来源与采集时点的只读材料，旧容器ID只作历史；新宿主按现有prepare协议冻结新service ID，原journal入history，不冒充新进程身份。

原VHD位于`D:\WSLDistros\Debian-Factory26\ext4.vhdx`，约45.9GB。离线ro,noload挂载取得原服务ID/manifest/journal、四份state存在事实，但新Sheet的status.json stat返回`Errno117 Structure needs cleaning`。该挂载未回放ext4journal，不能据此断言永久损坏。advisor建议一次隔离VHD副本正常日志回放以区分原因；D盘1.01TB空闲，Rebuild122.9GB空闲，原盘已分离，正在复制独立VHD。原发行版与生成不启动，不对原盘写修复，不升级e2fsck；若副本仍不可读则保留具体缺口并交回决定。迁移新增code.json仅为保存目录建立明确physical映射、snapshot_at和origin根，现有无映射归档仍报缺来源；代码映射错误独立于对象/原生阅读。

## 2026-10-01：单实例接入 WSL 当前现场

用户明确只有一个Console实例，主线经独立advisor核对后沿clean/hard cutoff授权收敛：复用WSL空service `c5c21595-811d-4dde-b6b4-83a77cf1bbc8`，完整复制两份Mac归档并保留原ID，先离线核对/register，再停止Mac PID56220并原子退役manifest、保存history，最后启动WSL唯一HTTP，原8765入口只保留独立SSH转发。原Mac归档不删除；没有新增跨宿主adapter、改源码或兼容层。WSL断线归档也不可用的取舍已向用户说明。

当前服务根 `/home/yyh/.local/share/factory26/exp-console/20261001-i13-live`。归档完整文件树hash、根Issue、对象、会话及原文回包迁前后一致，已登记真实GLM GitHub与Flash Sheet，各自runtime/对象/会话/native读取成功，其余按精确矩阵真实allocation、资源和数据库等待。没有测试comment、生成暂停/恢复或模型启动。IDs、PID、journal、后台操作参数、保护路径及Flash GitHub原生成容器退出边界归[I13单实例回执](../iteration13/console-launch.md)；本节的WSL部署已随原发行版删除而结束，以下各节的原Mac身份也仅作历史来源。

## 2026-10-01：正式路径路由完成

用户收敛：“我本质上只是想把路由理顺”，明确“不用保留现有参数的兼容和跳转”，并授权：“嗯，好的，你可以开始……是让 subagent 去做”。本轮由子Agent实现，保留Python后端，不迁移Node；移除query页面身份和自管history，采用React Router显式Home/run/issues/prs/agent/provider路径。query只允许实际筛选用途，本轮既有筛选仍为页面本地状态，不额外扩展持久化。

服务仅对合法页面结构提供SPA入口，未知页面/缺失静态资源/未知API保持404。React处理未知运行与对象、非法编号；深链刷新和前后导航统一走Router，草稿取消/丢弃和busy保护保留。无旧query解析或重定向。使用编译、真实登记归档HTTP和浏览器操作，不创建live、业务写入或模型运行，不编写/运行设施测试。冻结新根、核对旧进程和锁、保存history/config并退役manifest后部署；主Agent按最新明确commit授权规则收尾，不push。

React Router显式路径、Router blocker及Python严格页面入口已完成，旧query身份完全退役。Python/TypeScript/Vite构建通过；首页新增Router后546.34kB，有500kB提示如实保留。真实两份归档18条HTTP、Issue/PR与会话路径、刷新和前后导航已核对；最终Chrome无warning/error。主Agent独立发现的叶路由声明warning已修复并重新冻结，不只记录缺口。

当前稳定根`/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-path-routing-final`，service ID`4db9c009-e8d5-421b-97ec-b4e1e70c0705`，HTTP PID56220/PPID1。旧shadcn与中间路径服务已退出、锁核对、保存history并退役manifest；归档材料身份/存在记录一致，无业务写入或模型运行。当前仅两只读归档，草稿提交与busy现场边界不声称实际重验。完整范围、结果和证据见[路径路由回执](path-routing.md)。主Agent已独立复核实际HTTP、原文、刷新、前后导航及旧query退役，沿用项目明确自主git commit授权限定提交，不push；范围内实现和部署已完成。

## 2026-10-01：shadcn/ui 与 UI/UX 改进完成

用户直接指示：“请你改进 Exp Console：使其使用 shadcn ui 而不是 ant design”。此指示作为本范围开工依据，沿用本任务直接应用、部署与限定 commit 的授权，不 push。

范围为 web 的 UI 依赖、主题与页面组件：首页、运行选择、工作项、讨论、会话/原文、编辑预览及确认弹窗。采用 shadcn/ui 本地组件、Tailwind CSS、Radix 与 Lucide；删除 Ant Design 与其图标/样式/provider，不建立 Ant API 兼容层。App/Home 与 BraidRun/Sessions 的职责和现有 query 导航、草稿保护、revision/错误及单次写入语义保持。用户随后补充：“用 Shadcn UI 不只是死板地替换组件，还可以调整相关的 UI/UX 体验”。据此将范围扩到首页运行概览、工作项筛选与清除、归档说明渐进展开、会话原文优先及技术材料/Turn 历史折叠与分页；不只迁移组件外观。

实施按官方现有 Vite 接入，先完成可编译源码，使用真实已登记归档核验首页、筛选、Issue/PR、会话及原文深链、返回/历史导航和错误显示，再冻结新稳定服务根并切换 8765。保留旧服务身份、配置与 journal 来源，退役旧权威 manifest，不修改归档材料或建立另一现场。仅编译、构建和实际操作，不编写或运行设施测试。当前两份接入均只读；真实写入、草稿确认和 Docker 控制不能据此声称已验。

已移除 Ant Design 依赖、图标及样式/provider，接入16个官方 shadcn/ui 本地组件、Tailwind CSS 4 和统一主题。新增首页概览、工作项 Tabs/清除筛选、可展开归档说明、会话历史筛选/搜索；provider 原文置前，身份材料与 Turn 历史折叠，Turn 每页50条。Braid 详情按需加载，首屏 JS 为454.70 kB（gzip141.41 kB），TypeScript/Vite 构建通过且无大 chunk 警告。

真实 Chrome 操作覆盖两份归档的首页、Issue/PR、筛选、会话关系及原生正文深链。822条Turn显示17页并实际切到第2页；Pi正文首页加载24条记录，原文缺失归档保持具体HTTP400。首页/原文之间前后导航及首页刷新已核对，最终页面没有React warning/error；实际操作发现的重复React key已修复后重新冻结。10条只读HTTP回执中9条200、1条预期的原文缺失400；12个归档文件身份/存在记录前后一致。没有设施测试、模型运行或业务写入。

此批服务（已由上方路径路由制品接替）为 `/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-shadcn-ui-final`，service ID `97a16025-2f26-4032-b54e-98269264e8fd`，HTTP PID38698/PPID1，入口 http://127.0.0.1:8765/。冻结制品校验通过，前序home与中间迁移服务已停止、manifest退役，配置/active/launch及旧history接续到新根；journal未存在如实记录。保留两份原归档接入，不配置自启。

完成回执与剩余边界归[shadcn/ui 迁移](shadcn-ui.md)。原始证据入口：`runs/braid-console-control/20261001-shadcn-ui/`，含限定起点源码、完整工作区状态、构建、部署、HTTP、截图及导航回执。当前仅只读归档，可写草稿确认、保存/评论、暂停/恢复与Codex原文未重验；不创建现场补验。本批限定commit，不push；后续用户决定下一轮体验方向。

## 2026-10-01：Factory26 Exp Console 首页与架构收口完成

用户明确授权：“同意，不过这就意味着架构上要处理干净哦，你可以开工了（只是授权，你总是可以继续调查、规划、设计），不要阻塞主线。”本批独立实施、部署、实际核对与限定commit，不push，不重复索要开工。产品为薄的Factory实验入口，保留Braid专用详情；Console只拥有服务接入和显示状态，运行事实归lab/冻结材料，协作事实归Braid CLI/归档。

完成条件是Home永远可访问，零run有空状态与现有登记方法；列出已登记运行、live/archive和真实访问能力，进入Braid项及返回Home，保留既有深链/前后导航/草稿保护。来源、variant、实验名只展示明确材料事实，缺失未知，不猜目录或从Issue关闭推导实验终态。当前不扩非Braid、全历史迁移、自动发现、网页登记、实验启动/重试/调度、跨宿主聚合或adapter框架，也不因为改名搬整个目录。

用户随后明确修正：“不必保留原服务目录，甚至可以进一步改进服务目录等，建立一个干净的架构、实现，做hard cutoff”。按此撤销保留旧服务根/身份与schema兼容，使用新稳定根、新service ID、固定app和单一manifest；删掉stage/activate/rollback及旧自由registry入口。advisor重新复核引用交接：先准备显式两archive新接入，核实停止旧HTTP并保存配置/journal历史，原子退役旧manifest，再启动新服务。旧journal保留证据，不混入新活动journal；不删除历史实验资料，不自动迁移或回退，不制造永久双权威。验收使用编译、真实空登记和真实归档API/服务及可用浏览器；不建立或运行设施测试、mock、fixture、probe。浏览器policy仍阻断时如实记录，不换渠道绕过。I12已结束，本批不触WSL/VHDX、生成容器、模型或业务写入。

本批已完成源码、编译、真实空服务/归档HTTP及Chrome首页/深链/前后导航反馈，并hard cutoff部署到 `/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-home`。service ID `f5319ab4-537d-4cc4-9b21-26b911a859b8`，HTTP PID84660/PPID1，2026-10-01T02:31:44Z启动，入口仍 http://127.0.0.1:8765/。旧PID75619已核对停止，旧manifest已退役，历史配置/active/launch保存到新根history；旧journal不存在如实记录。最终只有新manifest的6条GC保护引用，归档文件前后身份一致。当前仅两archive，真实写入/草稿确认与物理控制未验，不启动现场补验。

本批方案、完成证据与未验边界归[首页与服务切换回执](home-entry.md)，原始材料在 `runs/braid-console-control/20261001-exp-console-home/`。起点Console代码已在55fe50a提交；保存当前源码与实际部署配置快照，保留TDD assignee及其它工作区dirty。

## 2026-10-01：清理归档与目标纠正

用户指出原数据已归档到本项目，要求核对执行记录。[WSL清理记录](../../runs/wsl-retained-20260930/README.md)明确保存main、i12-current、acceptance-workflow及official-local；最终步骤记载I12主动终止、WSL关闭、VHDX Full压缩480.62→71.17GiB，Debian停止。此前本会话“保留暂停并接回live”的假设已失效。GPT-5.6-Sol / Medium修复子Agent已停止修复，仅完成Windows只读诊断；未修盘、重建或恢复运行。

实际读取确认i12-current/control两份在线一致SQLite备份可读，分别有6/13条provider_sessions；2个根仓库及7个worktree的9份Git bundles可列refs，映射和dirty patches存在。约19:39采集的sessions/status/physical也保留，但没有标准native/manifest，不能声称已经具备Console原生正文归档接口或覆盖最终终止时点。副本restart目录下stopped/final-state.json实际指向更早fresh运行，不作本轮重启I12的最终停止回执。核对结果在 `runs/braid-console-control/20261001-service-start/cleanup-archive-review.json`。

用户进一步表示“可能没有恢复i12的必要了，我觉得”，主线同意保留已结束实验及归档，不恢复I12。修复方向改为恢复今后需要的可用WSL执行环境，并优先消费已归档历史材料；不强求全量恢复旧盘，I12恢复不是验收条件。旧VHDX问题与Console历史浏览分别处理；现有Mac服务继续可用。子Agent先核对非破坏修复、冷备及新环境选项，未授权覆盖旧盘或安装替代发行版。

## 2026-10-01：启动与跨实验接入（前序部署，已退役）

用户明确：“使braid console启动，我期望它可以控制多个run（且不必是同一实验）”，随后表示“debian已经恢复了”。现有registry按run独立登记，没有实验一致性约束；每项分别持有state、binary、workspace、访问及生成容器身份与权限。一个宿主可以在同一服务登记不同实验的live/archive；归档始终只读。受管理Docker控制仍要求同宿主daemon，跨宿主聚合不在本次实现中。

实际Windows列表仍为Debian Stopped，原WSL SSH端口122返回Connection reset。经Windows已有SSH入口启动Debian时，系统报告无法挂载 `D:\WSLDebian\ext4.vhdx`：文件或目录损坏、不可读取，代码 `Wsl/Service/CreateInstance/MountDisk/HCS/0x80070570`。这只记录本次系统返回，未执行磁盘修复、重新注册、容器启动/恢复或实验重建；此前拟恢复挂载并接回旧live的方向已被上方归档证据修正。

已启动本机 [Console](http://127.0.0.1:8765/)，稳定服务目录 `/Users/lanzhijiang/.local/share/factory26/console/20261001-55fe50a`，service ID `91f08b49-0698-4f05-89f6-9c226d3655fc`。冻结Python3.12和程序/前端，配置为目录内manifest.json，journal与轮转日志同属该服务。HTTP PID75619，经独立命令确认父进程为1且服务持续可读；没有SSH转发、登录自启或自动重启。停止只针对核对过命令与启动时间的此HTTP实例，不解除归档引用。

实际登记 `pi-archive-20260920` 和 `github-final-20260930` 两个独立保存运行；各自对象、根Issue和会话接口均HTTP200，分别为1/23个对象、1/215条会话。当前只有归档浏览，不把可读历史冒充live控制。自动浏览器访问因admin-enforced policy无法验证而被拒绝，未绕过；本轮页面交互未重验，沿用前轮同制品真实浏览器证据并记录本轮HTTP结果。

本轮对新稳定服务记录域执行只读GC plan，complete=true、6条依赖引用、零错误与零候选。未来GC扫描须纳入 `/Users/lanzhijiang/.local/share/factory26/console`；未扫描时须显式保护服务及其manifest引用，HTTP停止不解除这些引用。没有扫描历史运行域或apply。原始部署身份、只读HTTP、GC回执与WSL原始错误均保存在 `runs/braid-console-control/20261001-service-start/`。


## 2026-10-01：生命周期收敛开工

用户明确授权：“你可以开始委派收敛braid console了”。本轮由GPT-6.1-Sol / extra-high独立实现与收尾，不属于I13，不阻塞生成主线；已有自主git commit授权适用于本批，提交仅限定Console及必要GC/文档增量，不push。

目标是稳定服务归属、现场与归档读取边界、持久配置的依赖保护、HTTP/转发/访问容器的独立所有权，以及访问日志轮转和人工journal保留。advisor已先独立判断：归档不能直接运行可写CLI或依赖原Git，应读保存字段与manifest；HTTP停止不解除恢复配置的引用。本次使用新输出目录、真实已保留归档及本地只读实例取得反馈；不启动Debian/旧Console/I12、模型或业务写入，不运行历史GC、apply或清理，不移除旧容器。

当前实现、前序dirty归属及实际结果归[生命周期实施回执](lifecycle-implementation.md)。前序控制与会话导航未提交源码在限定快照中保留，并作为本次完整Console制品的既有依赖有意收纳；不将其当成本轮新行为或新验收。

## 2026-10-01：运行位置与生命周期复核

用户新增查看Console运行位置与架构，并明确重点是避免重蹈存储生命周期问题。已只读核对：本机8765无监听，Windows侧WSL列表为Debian Stopped、docker-desktop Running；原Console部署随Debian停止。旧registry的四个容器ID在Windows当前desktop-linux daemon均查不到，未启动Debian确认其它Docker环境。没有启动服务、迁移文件或操作I12。

[生命周期核对](lifecycle-review.md)保存架构、真实路径、引用与清理缺口：registry/journal和host binary仍在实验目录，CLI访问容器依赖原挂载，原生正文依赖原绝对路径，HTTP退出不接管访问容器清理，当前GC不解析Console registry。存储整合者已收到这些事实并在现有显式protect边界中记录；Console后续独立收敛服务资产、现场/归档浏览及引用释放，不把它加入I13。当前回执在 `runs/braid-console-control/20261001-lifecycle/`。

## 授权与目标

用户本轮原话：“console 问题不纳入 iteration 问题；console 修正可以立即应用，应该让 braid 和 braid console 之间存在清晰的边界，让他们可以相对独立地迭代；braid console 属于实验基础设施的一部分。”
主线据此授权 Console 整体暂停/恢复控制及暂停后人工读写的必要修正，允许实施、部署和实际操作验收，由主线统一提交。用户随后明确：“braid console的修改方案不需要我复核，可以直接应用。”
不得为了验收解除暂停、发测试评论或改变生成内容。此授权最初要求两条I12都保持暂停；19:25:33 CST的Console journal曾记录GitHub被用户恢复，用户随后再次暂停。20:52 CST真实API读取确认两题均暂停，以[I12 packet](../iteration12/packet.md)及实际控制读取为准。本次接续与前端部署不改变现场控制状态。

目标是让用户能冻结当前运行的全部 Agent 会话及 Braid 定期检查，同时保留原代码、Git、对象和原生会话；人工查看、编辑及评论使用原现场，恢复只由用户明确操作。

## 职责与最小实现

Braid 负责对象、Git、事务和事件投递，接口仍是配套 CLI。Console 负责页面、人工草稿、操作回执；Docker 运行适配层负责固定容器身份下的物理暂停和恢复。Braid 不依赖 Console、实验名或 ARC，本次不修改 Braid 调度、数据表、事件语义或生成材料。

前一支线已将对象 CLI 改为每 run 一个独立、无网络的访问容器；根因、一次性容器的实际失败及稳定读取证据见 [暂停后访问历史记录](../iteration13/console-paused-access.md)。本次沿用两条既有访问容器，不创建或复制另一份 state。
新增明确的 Docker registry 配置，分别登记生成容器与访问容器的完整 ID、容器内 binary/state。对象基础命令由该配置生成；物理控制只使用登记的生成容器 ID，浏览器只提交 run ID 与 pause/resume。
页面独立查询生成状态、显示暂停/恢复按钮；恢复前说明会继续全部会话、定期检查和已入队人工输入。物理状态查询失败不阻断对象查看，也不把缓存状态当控制成功。

为避免新的暂停冻结 SQLite 写事务，适配层在同一 Linux 访问容器、同一挂载数据库中取得 BEGIN IMMEDIATE 写者门闩；持锁调用 Docker pause 并确认实际 Paused 后，再 ROLLBACK 释放。门闩不修改任何行，也不读写 Braid 私有表。生成与访问容器的数据库挂载必须一致，当前库必须使用 WAL。
每 run 的 Console 操作锁串行化物理控制及对象修改的前置读取到执行结束。若写者门闩不能取得，不发新暂停命令；若 Docker 结果或门闩释放未确认，保留原错误及 journal，不自动 unpause、解锁、删 WAL/SHM 或重试。
已有的直接 Docker 暂停可能发生于写事务中；对已暂停运行重新请求 pause 只核对现存写者锁，不解除或重新施加暂停。该核对不等于业务修改已验，也不能倒推历史暂停经过了新顺序。

独立 advisor 已复核上述正常路径，无需新增 Braid 暂停协议；其要求是门闩共享 Linux WAL 锁域，并处理超时、EOF和异常释放。数据库写者门闩只保证暂停边界未冻结写事务，不代表全部文件或应用已经到达可恢复检查点。

## 实施与验收范围

改动在 braid-console/server.py、docker_runtime.py、web/src 的运行控制 UI/API，以及 README 和部署说明。物理控制与对象写入共享原 journal，采用 started、completed、failed 或 unconfirmed 回执；不另建控制数据库或调度状态机。

验收使用 Python/TypeScript 编译、现有真实 Console API与浏览器，以及当前两条暂停运行的 BEGIN IMMEDIATE→ROLLBACK。允许再次请求 pause 核对写者锁，保持原 Paused；不发送业务 POST，不恢复生成，不建立或运行设施测试、模拟测试、smoke或自检。
必须记录实际两题对象读取、写者锁回执、页面控制及人工输入入口、最终原容器暂停状态，并保留版本、registry及服务身份。
新运行状态下的暂停顺序、真实 resume 和实际评论/编辑提交，在本次保持 I12 暂停的范围内均不能实测；交付中明确区分这些边界，不声称已完全验收。

## 部署与实际结果

Python 源码编译、TypeScript 编译与 Vite 构建成功。构建仍提示现有主 bundle 超过 500 kB；本次没有引入依赖或扩大为构建优化。没有建立或运行设施测试。

已部署到 WSL `/home/yyh/Development/factory26/braid-console/`，服务 PID 从 111070 替换为 **204242**，仍监听 `127.0.0.1:8765`。Mac 的既有 SSH 转发入口是 [Console](http://127.0.0.1:8765/)。部署使用 `runs/iteration12/restart-20260930/console-runs.json` 与原 `console-actions.jsonl`；registry 从自由 CLI 参数改为固定 Docker 配置，原 state、binary、run ID、权限及访问容器保持。前端实际资源为 `index-YblaaaWX.js` 与 `index-D_SK0Cwi.css`；源码及资源 SHA-256、部署命令、旧服务备份和新服务日志见原始证据。

两条真实 `POST /api/control` 的 `pause` 均返回 HTTP 200、`changed=false`、`writer_lock=available`，journal 分别记录 started→completed。这证明在原容器保持暂停时，同一现存库可取得 `BEGIN IMMEDIATE` 并完成 `ROLLBACK`；没有执行 unpause，也没有执行新的 Docker pause 命令。

| 实际读取 | GitHub | Sheet |
| --- | --- | --- |
| 列表 | 9 个 Issue、1 个 PR | 6 个 Issue、2 个 PR |
| 根 Issue #1 | revision 3、6 条评论 | revision 5、2 条评论 |
| 已有 PR | #2：revision 1、0 条评论 | #8：revision 1、4 条评论 |
| 原生成 PID | 5217 | 5181 |
| 最终原生成状态 | Running=true、Paused=true | Running=true、Paused=true |

实际 HTTP 记录包括 registry、两题物理状态、两次幂等暂停、列表、根 Issue 与已有 PR，共 13 条全部 HTTP 200，耗时 0.345–1.529 秒。暂停后的对象 revision 与评论数和此前读取一致。最终 Docker 核对确认原容器完整 ID、PID 和 StartedAt 未变；两访问容器均只有 `sleep infinity`，网络为 none、无自动重启，临时写者门闩已退出。

使用新的 Chrome 临时标签实际打开两题根 Issue，页面均显示“生成已暂停”“恢复生成”，列表和正文已加载，编辑按钮、external 评论输入仍在。Sheet 可见错误列表为空、评论输入未禁用；未点击恢复、保存或评论提交。两题截图及可访问状态保留在本次工具记录，临时核验标签已关闭，用户原页面未操作。

原始证据在 Mac 和 WSL 的同一相对路径 `runs/braid-console-control/20260930-control/`：`deployment.json`、`source-manifest.json`、`console-runs.deployed.json`、`http-operations.json`、`control-journal.json`、`final-container-states.json`、`browser-observation.json` 与 `server.log`。HTTP 文件保留具体路由、输入、状态、原始正文及耗时；浏览器 observation 是实际界面观察摘要，不能替代业务提交回执。

可重复的实际读取入口如下，恢复和业务写入需由用户决定。对于本次两条已暂停运行，可先读取 `/api/runtime` 确认 `paused=true`，再按 README 的 `/api/control` 请求 `pause` 取得幂等写者锁回执；不能将其改为 `resume` 用作验收。

```sh
curl --fail-with-body 'http://127.0.0.1:8765/api/runtime?run=i12-restart-github'
curl --fail-with-body 'http://127.0.0.1:8765/api/items?run=i12-restart-sheet'
curl --fail-with-body 'http://127.0.0.1:8765/api/item?run=i12-restart-sheet&kind=issue&id=1'
```

新运行状态下的“持写者锁→Docker pause→确认→释放”、真实 resume、实际评论/编辑及之后 Agent 消费仍未实测。当前证据只确认暂停后的读取、写锁可取得和 UI 入口；不能声称业务写入或全生命周期已验。已有直接 Docker pause 若冻结了写事务，本实现报告具体锁错误并保留暂停，需要用户决定是否恢复；本次两题未遇到此锁障碍。

当前无源码或部署阻塞。后续按用户明确的恢复或人工业务操作取得相应真实反馈；本支线不恢复生成，也不改 Braid 调度或 I13 内容更新策略。

## 后续新 CLI 接入边界

I13 已将 Braid `resolve/unresolve` 收窄为只接受讨论根 ID，见[CLI实施](../iteration13/cli-implementation.md)。
当前 Console 绑定的仍是 I12 冻结 binary，保持原运行与读取能力。`Discussion.tsx` 的整串 resolve/unresolve 已集中到根讨论入口并明确范围，回复保留单条hide，不在服务端隐式转换编号。源码、前端构建与20:21 CST部署完成，实际页面读取已核对，真实写操作仍未验，见[实际实施记录](cli-root-actions.md)。未来切换新binary时复用此入口。
这项接口适配属于 Console 自身，不能为适配而恢复 Braid 的隐式扩大作用范围，也不改冻结 I12。

## 会话关系导航

用户新需求：“Braid Console 有新需求：我希望看到 issue/pr 相应的 agent session 以及 agent session 相应的 provider sessions（包括历史的）（可能需要引入页面路由管理框架）（仍然交给 sub-agent GPT-6.1 extra-high 去实现；不阻塞主线）”。沿用“braid console的修改方案不需要我复核，可以直接应用”的授权，本轮独立实现、部署并只读验收；未授权 commit/push。

用户随后要求“还要能阅读原生对话和工具调用内容”，已纳入原生历史文件按需分页读取。21:14 CST源码与前后端部署完成，服务PID **483894**，新资源 `index-BROGd5Gi.js` / `index-PdJYewCM.css`，原registry/journal、冻结binary、state和生成容器保持。两题前后均暂停，未业务写入、跑模型、commit/push。

冻结 I12 的 `status --json.physical_sessions` 给出工作项、`group_id`、assignment generation、provider/native 身份及生命周期、turn历史。`group_id` 经CLI源码SQL核对对应持久 `agent_instances.agent_id`；同一Braid agent下保留多次provider替换历史。该接口从physical目录枚举，再补充数据库映射；不证明缺失physical材料的数据库记录也已列出。本次独立只读诊断确认当前两题数据库provider/agent身份与inventory逐项一致，但GitHub1条、Sheet2条原生日志已缺失，接口明确返回FileNotFoundError并保留元数据。

Python/TS编译与Vite build通过；历史Pi原生正文真实GET、第二页、稳定offset与刷新、工具call/result ID对应以及资源hash均完成。浏览器Chrome初始化报 `codex app-server exited before returning initialize`；IAB管理策略安全检查不可用并拒绝访问，未绕过控制。直链重载、后退/前进及取消离开后的草稿保留尚未实际UI验收；当前两题全部provider为Pi，Codex未实测，非文本工具block只呈原生JSON。实现、部署与具体边界见[会话导航](session-navigation.md)，原始证据在Mac `runs/braid-console-control/20260930-session-navigation/`。

主Agent独立部署后GET也确认两题暂停、原PID未变，列表26/13及历史正文首页各50条无错误，证据 `primary-readonly.json`。当前源码与部署可行范围已收尾；剩余浏览器交互验收由工具可用性阻断，3份原生日志缺失保持原现场、Codex真实验收等待相应运行材料，不扩展Braid接口或启动模型。
