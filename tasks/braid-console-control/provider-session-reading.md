# Agent Session 对话与代码阅读方案

2026-10-01。用户已明确授权开工、限定提交与现有实例重部署，并在外部环境变化的树形整理后明确同意继续。本轮实现、编译、Debian-Rebuild原生部署及两条新GLM现场的真实Pi阅读验收已完成；旧Console记录不迁移。最新状态以packet开头为准。用户希望Provider Session更接近Chatbot，同时保留高级trace能力，随后增加Agent Session当前工作区文件和origin各分支代码阅读。范围为只读会话与代码阅读，沿用真实实验现场。

## 观察与问题

方案形成时，`Sessions.tsx` 将原生 user、assistant、toolResult 逐条渲染为同级卡片，工具调用参数默认展开。页首以 native UUID 和 provider 恢复路径作为主要身份；普通正文也被限制在 450px 的独立滚动区域。读者需要反复穿过技术信息和大段工具输出，才能找到 Agent 的可读回复。

本轮只读查看了正在登记的 GLM GitHub 会话，并保存前两页共 100 条原生记录：2 条 user、40 条 assistant、53 条 toolResult，另有 5 条原生事件。其中只有 16 条 assistant 包含可见 text。两条 user 分别是 Braid 工作项上下文和自动更新，不能标为人类的“你”。一条 assistant 正文为空，但具有 `stopReason=error` 和具体 HTTP 400；另有一条工具错误。

53 个工具调用与结果在已加载区间中可按 ID 关联。`call_d69a87c44ab84baf80748e0d` 的调用位于第一页字节 330475，结果位于第二页字节 341840；返回内容只是异步子任务启动回执。配对成功只能证明工具已返回，不能证明子任务完成。样本还有两条 `custom_message/subagent-notify/display=false`。未观察到原生分支或压缩；此事实不证明其它会话没有这些情况。

原始证据在 `runs/braid-console-control/20261001-session-reading-design/`，包括 `sessions.json`、`live-page-0.json`、`live-page-1.json`、`shape-summary.json` 和 `observations.json`。原生 reader 已脱敏；这次取证没有业务写入、运行控制或模型调用。

## 推荐的阅读体验

Provider Session 默认打开“对话”，旁边保留“Trace”切换。同一份原生记录驱动两种呈现；切换不重新建立会话或读取另一份内容。标题使用可识别的 profile/provider，UUID、恢复路径、revision 和材料入口归入现有技术详情。Braid 持久生命周期与实际生成状态继续分开呈现。

对话采用连续的单列阅读：原生 user 标为“输入”，assistant 的可见 text 标为“Agent”，使用既有 Markdown 渲染并自然展开。只在材料明确支持时标注输入来源，不用关键词猜测是不是人类指示。不添加消息输入框，不生成替代原文的模型摘要。

工具和思考进入就近的折叠活动区，只有过程内容的 assistant 不产生空白回复。连续过程可以合并为活动组，遇到正文、输入或原生边界就结束该组；混合消息保留可见 block 的相对次序。活动摘要来自原生工具名、调用数量和明确错误标志，不猜测任务进展。

每个工具可逐层查看参数与结果，工具卡片以调用的原生位置为锚点，结果引用自己的来源记录和时间。普通工具结果不另占一张顶级对话卡片；未匹配或关联有歧义的结果仍有独立入口。状态只写“已返回”或“已加载记录中未见结果”，不从缺结果推断执行中或失败，也不把后台启动回执写成完成。

思考默认折叠，原文按需展开。`display=false` 的后台通知保留为活动中的通知入口，不改写成用户或 Agent 发言。图片等当前不能解释的内容保留非文本内容提示及原生查看入口；这轮不新增图片渲染。

错误在对话默认层仍然显著可见：包括空正文 assistant 的 `stopReason/errorMessage`、工具 `isError`、JSONL 解析错误和读取失败。普通活动折叠不能隐藏存在错误的事实。保留具体 HTTP 状态、原因与可展开诊断内容，继续应用已有脱敏。

## Trace 与技术边界

Trace 保留现有文件顺序的所有记录：原生事件、工具参数、结果、思考、错误、完整脱敏 JSON 和字节位置。对话消息与工具提供“查看 Trace”，在同一 provider 页面切换并定位来源记录；调用和结果有各自定位点。返回对话时保留阅读位置。现有会话路径不变，本轮不新增路由身份或跨会话聚合。

读取继续使用现有 `useInfiniteQuery`、`NativeEntry.offset` 和 `/api/transcript`。关联从所有已加载页派生，不逐页独立配对，不保存新的内容副本。技术读取边界、身份核对、完整行处理、分页限制和凭据脱敏由现有后端持有。

Pi `parentId` 不连续、`branch_summary`、`compaction` 等边界需要显式标记，不跨边界合并活动或猜测配对。父链比较包含视觉上隐藏的原生事件，不能只比较对话正文。首版呈现按文件记录顺序阅读的历史，不承诺重建当前有效分支。无法解释的格式保留 Trace 入口与具体提示，不能显示成空会话。

Braid Turn 历史没有 native entry 映射，继续作为独立技术详情，不把 native 消息归为 Braid Turn。Codex 原生材料与 UI 尚未真实验收，不以当前 Pi 样本宣称跨 provider 对话呈现完整。

首版保持从会话开头向后分批读取、手动刷新。页面明确显示“当前显示会话开头，后面还有记录”及已加载范围，顶部和底部都能加载后续。“刷新已加载内容”与“加载后续”是不同操作；局部末条不代表会话最新进展。最新优先、自动尾随及倒序读取不属于这次阅读提案；如果主要使用场景变为立即判断 live 会话刚刚发生了什么，应重新将最新定位列为必要能力。

会话正文继续复用当前读取协议；新增文件阅读需要扩展 Console 的只读后端和前端文件组件，撤销原提案“后端无需改变”的范围判断。工作项操作、Braid 调度、Git 工作区生命周期与部署协议不因此改变。实现准备时按实际职责安排 transcript 和文件组件，不建立通用 provider 框架或新增编辑器依赖。

## 工作区与 origin 代码阅读

Braid 的本地运行契约明确：`state/origin.git` 是该次运行共享的裸 Git 仓库，每个工作项在 `state/worktrees/` 使用独立 clone，提交只有 push 后才进入共享历史。它不是另一个 GitHub 服务。工作项改派会保留并交接原 clone，Provider Session 替换也不代表产生独立文件快照。依据是 `sources/braid/docs/20-product-tdd/local.md` 第 11、81 行，以及 `worktree.rs` 和 `store/mod.rs` 的实际交接逻辑。

2026-10-01 16:27 CST，通过当前唯一 Console manifest 登记的 GLM 访问容器复核：origin 确为 bare repo，根工作区是独立 clone，remote origin 指向该裸仓库；工作区顶层已有 `docs` 和 `packet`。当时 origin 的 `main`、`develop` 都指向 `9eb1f3b94a23952cfd3313c2d132aeca66838480`，提交树为空。这是现场观察，不是对后续进展的判断，也不能据此推断工作区文件已提交或已发布。完整命令回执保存于 `runs/braid-console-control/20261001-session-reading-design/workspace-origin-readback.json`。

推荐在 Agent/Provider Session 内增加“文件”入口，文件区明确选择“会话工作区”和“origin 分支”，均使用目录树与正文阅读区。origin 同时提供运行级入口，因为它属于整个 run，不应要求用户先找到某个 Agent 才能浏览。文件、对话与 Trace 各自保留阅读位置，文件读取错误不阻断会话阅读。

| 来源 | 展示内容 | 时间与身份 |
| --- | --- | --- |
| 会话工作区 | 登记目录中的实际文件，包括未提交、未跟踪和 Agent 私有工作材料。 | 展示工作项、登记会话、目录来源和读取时间。文件仍可能被 Agent 修改。 |
| origin 分支 | 本次运行共享仓库中各 `refs/heads/*` 的已发布提交树。 | 选择分支时固定完整 commit；目录和文件一直读取同一 commit。 |

工作区入口从 CLI 已返回的 `worktree` 绑定读取根目录，不由浏览器指定绝对路径，也不根据 profile 名称拼接目录。Agent 下若有多个不同登记目录，明确列出供选择，不按最大 generation、数组顺序或 provider lifecycle 猜测当前目录。若只能确认某历史 provider 的登记路径，页面写“该会话登记目录的当前文件，非历史快照”，不声称旧 Agent 仍拥有该目录。工作区从工作项延续的事实不能代替当前归属的证据。

工作区按实际文件系统逐层列目录、读普通文件；显示当前 Git 分支只作说明，不在此切换工作区分支。刷新重新读取当前目录或文件，注明读取时间；多文件浏览不承诺同一时刻的完整快照，不为保持浏览一致而暂停生成或复制整个工作区。`.git` 不作为代码树浏览；未提交和未跟踪文件不能被 Git 提交树过滤掉，`.braid` 等私有工作材料也不能因未跟踪而自动消失。

origin 从服务已登记的执行 namespace 下 `state/origin.git` 读取，不借用 Agent clone 的 `refs/remotes/origin/*` 缓存，也不根据 Agent 可改动的 remote URL 选择浏览根。分支列表返回完整 ref 与 OID；选中后，目录、文件与前端缓存都使用该完整 commit。页首持续显示“分支名 @ commit”，显式“更新到分支最新”才切换版本。分支继续推进时已打开内容保持原版本；空树显示空树，缺对象保留具体错误，不能自动改读工作区或最新分支。

实现复用登记访问容器或受管理本机执行环境，用固定参数的 `for-each-ref`、`ls-tree -z`、`cat-file` 读取 Git 对象；不为浏览执行 checkout、fetch、clone 或 worktree 物化。尤其不能复用 `worktree::resume/provision/verify_existing` 作读取校验，这些函数会写 Git 用户身份或 `.git/info/exclude`。本需求不依赖 `git status`；若实施准备确定需要文件修改标记，相关读取必须禁用 Git optional locks，避免刷新索引。

新增读取边界属于 Console：浏览器提交已登记来源、相对路径，以及 origin 阅读所需的 ref/commit，服务核对来源并决定实际根目录。目录按需展开，不递归扫描整个实验。工作区读取拒绝越界、不跟随符号链接，不读取 FIFO 等非普通文件；符号链接只显示目标信息。Git tree 中的符号链接与子模块也只展示其保存身份，不 checkout 或递归读取外部目录。正文有界读取，超大或二进制内容显示具体限制，不静默截断成完整内容。代码和 HTML 按文本呈现，Markdown 使用已有安全呈现，不执行文件或 Git filters；凭据值继续按现有具体脱敏规则隐藏。

取材时的两份旧归档都没有保存 `braid-state/origin.git`。Pi 归档保存的一个工作区样本仅包含 `.braid/` 和 `.git` 文件；GitHub 归档没有 `worktrees/`，`work/` 只有 native homes。因此本轮不能把它们展示为完整 origin 或当前工作区。归档只有在保存材料与原目录有明确映射、范围可确认时才能显示“保存的工作区”；未保存来源明确提示缺口，不回退旧绝对路径，不修复或重建仓库，不拿最终 application 代替所有分支。新增归档保存或迁移不包含在这次阅读方案中。

## 可复核草图与验收

交互草图为 `runs/braid-console-control/20261001-session-reading-design/prototype.html`，使用保存片段展示正文、折叠活动、显著错误和 Trace 定位。草图明确标注示例节选，不能代替真实实现或完整原文。部分事件为了展示不同状态放在同一屏；它不是原生时间线。

草图已生成，浏览器拒绝 `file:` 地址，理由为仅允许 `http:` 与 `https:`，并明确禁止绕行。本轮没有改用服务器或其它浏览器规避此限制，只请求在 Codex 文件面板打开源文件。因此草图交互尚未经过实际浏览器核验；原有线上 Provider Session 的页面观察已完成，两者不可混同。

原草图目前只演示对话与 Trace；新增工作区/origin 的产品结构和读取边界由本文描述，不能据此宣称文件阅读界面已实现。

实施后的验收使用 TypeScript/Vite 构建、实际已登记会话的只读接口与浏览器操作。核对正文顺序、长正文阅读、活动展开、错误默认可见、跨页工具配对、调用/结果各自 Trace 定位及返回位置，并确认缺日志时保留元数据和具体错误。文件验收覆盖现场工作区文件与 origin 空树的区别、两个已发布分支的选择、固定 commit 的目录与正文一致性、缺来源和历史会话提示，以及文本/目录读取失败、符号链接和非普通文件边界。真实非空分支代码通过已有已发布材料验收，不能为此向生成现场写入样例提交。另检查深链刷新、返回导航和窄屏布局。按仓库规则，不创建或运行设施测试、mock 或换名自检，不为验收启动模型或修改实验业务数据。

对话以及新增文件来源、生命周期与只读边界均经过独立 advisor 核对。用户开工原话为“同意，你可以开始了。你可以自由提交，也可以随意重新部署现在的那个实例。”此授权覆盖本文范围、构建与实际验收、当前唯一实例重部署和本任务限定提交，不push或操作模型运行。已新增Transcript和FileBrowser、Console只读代码reader及接口，并复用脱敏；TypeScript/Vite及Python编译通过。验收和部署证据归`runs/braid-console-control/20261001-session-reading-implementation/`。部署阶段用户先明确改为Debian-Rebuild，随后确认已彻底删除Debian-Factory26，并要求不迁移旧Console运行记录，从干净基线重头开始；I13-GLM两项由用户在Rebuild重新启动。因此原六条接入、旧journal搬迁及VHD恢复不再是本轮完成条件。迁移专用归档代码映射和临时VHD/脚本已清理。用户在树形整理后回复“是的，没错，按这个推进”；已按既有prepare/serve在Rebuild建立原生Python服务，实际HTTP返回空登记列表，浏览器空首页无warning/error。随后按两项新运行的精确allocation和实际namespace接入，完成下方真实阅读验收，不改变实验生成。

新宿主实际采用named volume和stage子目录，且Console用户不能遍历Docker数据目录。独立advisor确认共享mount来源应统一加上经volume/目标匹配的Subpath，Docker存在性检查在已核对身份、所有权和挂载的访问容器内执行。登记保留准确宿主路径供GC，本机目录和受管理binary检查保留。访问容器与原runtime使用同一named volume及子目录，保留Docker消费者引用；无需提升Console权限、改变Docker目录权限或添加跨宿主适配层。两项接入和实际读取均已通过。

## 真实实施与验收结果

部署改为用户指定的Debian-Rebuild原生Python，先核对空登记Home，再按新实验operation和真实资源接入GitHub、Sheet。最终service为`4161a417-fede-4be5-b692-162350a3d826`，稳定根、两条完整lab run ID与操作回执见packet；生成binary SHA-256为`5e98b9374d20870fc6dd45406b4b2d4efc41bf9e6fbb9f3edd4ff64ae8f50a73`。旧HTTP、manifest和访问容器已核对停止或退役，仅新manifest为权威。12个冻结程序和前端文件与本地逐项一致。

真实验收覆盖以下可观察行为：

- 两条运行的对象、会话、原生正文、工作区和origin接口实际读取成功。GitHub首页50条、下一页50条；跨页工具`call_d69a87c44ab84baf80748e0d`在字节330475发起、341840返回，页面分别跳转并突出对应Trace。返回状态写“已返回”，异步工具确认不被改写为任务完成。
- 空assistant的HTTP400错误及`isError=true`的bash错误在默认对话直接可见。正文以输入/Agent呈现，思考与活动默认折叠，后台通知仍保留。Chat与Trace来自同一分页原文，原始JSON可展开。
- 实际操作发现返回Trace时顶部页签移出视口会干扰位置保留，使用CSS sticky页签解决。最终稳定切换中Trace位置17192、Chat位置2160，返回Trace仍为17192；调用与结果的各自字节定位均可用。
- Agent及Provider工作区可读取当前未发布文档，Markdown源码/预览切换保留阅读位置。历史provider路径与新provider相同的实际样本按目录去重，并明确当前内容不等于历史快照。origin的main空树保持真实空树。
- GitHub后来已发布的develop固定`726e21f4ea42ff9a5dbedd572a86fd1bf0bb2ed1`，`docs/architecture.md`为9788字节，内容SHA-256为`a1864d303625a71bd13b09e2dc4bcc38e9c3718c0ab4c9868d4dd904a7531dec`，与当时工作区对应文件一致。刷新分支列表保留commit；切到空main再返回develop保留文件路径与版本。Sheet也实际读到非空develop；生成后续提交可继续变化，记录中的commit只表示验收时版本。
- 运行级origin弹窗保留工作项草稿和URL；本次人工验收草稿已清空，未提交业务内容。Provider深链刷新及浏览器前后导航通过。390px文件树与正文实际单列，对话宽度从860px溢出修为容器100%宽度；真实长消息加载后页面宽375px、正文305px，无横向页面溢出。
- 实际代码接口拒绝父目录、`.git/config`及将分支名当commit，均返回具体HTTP400；不存在文件保留FileNotFoundError及响应详情。最终浏览器无warning/error。

TypeScript/Vite和Python编译通过。保留现有546.35kB入口chunk提示，没有为本轮添加依赖或代码拆分框架。未建立或运行设施测试、mock、probe或self-check；实际API、Docker身份与编译分别取得独立反馈。没有暂停/恢复生成、提交业务消息或启动模型。两条原runtime的完整ID和StartedAt保持，最终Running且未Paused。

原始结果在`runs/braid-console-control/20261001-session-reading-implementation/`：`release-deployment.json`、`release-identity.json`、`release-http.json`、`code-boundary-reads.json`、真实分页/文件响应和`provider-chat-release.jpg`、`origin-files.jpg`、`mobile-chat-release.jpg`、`mobile-files.jpg`。部署中先前日志目录缺失及sleep PID1停止超时属于操作脚本错误，原错误和中间身份已保留；新访问容器加`--init`后停止与替换成功，没有修改Docker停止协议掩盖错误。

本轮真实材料为Pi，Codex及非文本内容没有新增实际样本；多个不同登记worktree、symlink/FIFO/binary/非UTF8、partial-clone/promisor拒绝及分支在固定阅读期间再次前移没有真实现场例子，不声称这些分支已实测。路径边界经实际接口核对，其余保护保留源码与编译证据，不制造文件或修改origin补样本。最新定位、自动尾随、代码编辑、原生消息发送、归档映射及历史数据迁移不属于已批准范围。

Console访问容器持有真实named volume引用，实验资源清理会因仍有消费者而保留具体未确认结果，生成和评分结果不受影响。最终清理按README的关闭HTTP/转发、停止访问容器、release接入、明确移除容器、实验清理顺序执行；只停止不能解除volume引用。此生命周期边界已由advisor核对，Console不承担实验runtime清理。
