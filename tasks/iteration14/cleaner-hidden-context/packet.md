# Cleaner 隐藏评论上下文修复

当前状态：用户最新要求收束实验基础设施，已停止所有新增冻结、prepare、launch和模型请求。最终恢复包已装配，但未执行prepare、未启动runtime、未发送通知；先前启动授权不再自动接续。制品与停止交接见 `runs/iteration14/cleaner-hidden-context-20261002/stopped-handoff.json`。

2026-10-02。用户经主会话明确授权：“独立会话立即修复隐藏评论上下文膨胀并至少热部署到I14 cleaner”。范围为模型 context 投影、真实运行读回和该 cleaner 的保全热恢复，不启动新实验矩阵或恢复暂停 dispatcher。

现有 `render_context_comments` 仅折叠 resolved 后代；hidden 分支仍逐条输出作者、祖先与重复理由。改为省略具有 hidden_by 的后代，将自身隐藏的分支根按完全相同的可选理由聚合为一行。root hidden 状态保留；中间节点 hide 只缩减其分支，保留其它可见回复。已 resolved 前缀仍按现有 cutoff 规则处理。原始数据库、正文、hide/resolve 和 CLI 追溯语义不变。

授权运行是 `pi-braid-i14-cleaner--hackathon--github-51de01f10f57f3`，具体实际身份以原 operation、run 与 Docker 读回为准。证据私有目录为 `runs/iteration14/cleaner-hidden-context-20261002/`。主会话拥有资源保护和内存采集等公共改动，本会话不改其源文件，编译时包含完成后的共同修复。

验收使用编译、同一真实 SQLite 快照的旧/新 context 读回、原始评论及线程映射，并保存停写、完整工作区与 Git/数据库/WAL/native 身份。hide 不会清除旧原生历史；不为本次显示修复制造 description 修改或改写原生历史。恢复后实际发送的新输入与历史保留分别报告。禁止测试、smoke、probe、第二采集器及隐藏评分注入。

下一步：实现 renderer 和契约，独立编译 Linux 制品；读回并保全 cleaner，使用既有恢复 operation 接续且核实无双 writer。当前没有可确认的较早完整检查点，选择最近完整停止现场，不凭 Git 或 DB 单件回滚。

## 已取得的反馈

独立 advisor 确认最外层隐藏分支代表和 resolved 截止规则，未要求对象语义变更。本机及 Linux 编译成功；Linux binary SHA256 为 `63fdabce78498bf6164df846308d05c11f640cd844c544f561507d1df82f7e8d`，源码 SHA256 为 `ee2024f9532a50fad021a8c14cb03eb1b699ed4d1b1075f6faccaceb0fe848d5`。逐文件与共同修复制品比较仅 `src/context.rs` 不同。

同一暂停现场 root Issue 1 的旧/新投影分别为 10,696 / 4,833 bytes，估算 token 为 2,892 / 1,427；77 条完整同理由隐藏评论汇成一行。Linux 新 binary 与本机投影逐字一致，77 条隐藏评论原正文仍在 SQLite。证据见私有目录 `context-readback/{before-issue-1,after-issue-1,linux-after-issue-1}.md` 和 `comparison.json`。来源没有隐藏回复，隐藏 thread、嵌套 hide 和 resolved/hidden 重叠尚无该 run 实例，不把编译或源码复核当运行验收。

Docker 实际标签、daemon、StartedAt 与原 operation/run 对齐后，来源容器已 pause；完整现场通过原 helper 导出，尚未启动接续。原生历史不删除，不人为修改 description 触发重建。ARC-only cleaner 新 base 已装配，恢复规格仍使用原模型配方、2GiB/2CPU、五槽共享准入及原 self_funded 完成后应用重放。

## 保全顺序调整

原 I13 导出脚本对全部运行依赖先逐文件哈希，在远端冷 I/O 上持续等待；已确认终止本会话的只读扫描后，改为通过原 helper 一次完整 tar，不排除任何持久文件。归档包括 PR2 的 `core.35086`（1,046,609,920 bytes）和 `core.36760`（1,061,806,080 bytes），不从路径猜测崩溃原因。辅助全树双重哈希不作为保全门槛，完整复制、成功解包、关键身份和原 volume 保留作为恢复前提。

已核实原 volume 的三个消费者：生成容器、原 helper、cleaner 专属 Console 访问容器。为封住外部 CLI 写入，只停止访问容器 `f3a6eabbad722015cc5a8747a52829ce45ec1964beab6e3c6fa1aea0c17c1d3e`，不停止共享 Console HTTP 或其它入口。Console 的登记规则禁止用旧运行 ID 重新指向另一现场，恢复登记交由主线/Console owner 协调新物理 run 与来源关系，不能现场改写旧登记。

独立 advisor 复核后，将来源物理停止提前到同一次 tar 传输期间，以释放冻结来源已观察到的 871MiB 内存，不宣称必然提高 I/O 或证明 OOM。旧 Mac adapter 按 host/boot/PID/birth/PGID 核对后 SIGSTOP，阻断自动清理；原 volume/helper 保留。2026-10-02 10:36（上海）来源直接 KILL，未 unpause，已读取 `Running=false`、`Pid=0`、`ExitCode=137`、`OOMKilled=false`。这是主动热切换，不是新增不明 OOM。停止原件为 `source-stop.json`，访问入口和旧 adapter 的停止原件另存。

原导出程序的“结束时仍须 paused”检查会拒绝本次已明确停止的来源，不能将这条预期拒绝当复制失败。复制退出0并完整可解包后，再以独立停止回执完成归档认证；原始归档和原错误均保留。新 writer 仍需完整归档与离线 prepare/readback，通过后才启动。实际来源 UID/GID 为501:20，prepare 显式冻结相同值，镜像也使用原 image ID。

完整原始归档 4,771,814,912 bytes / 90,504成员，SHA256 `feec5156ee400ffb1f3c04fd71e0134fa7576c16e5155b21a7173c9e08ccb564`；完整解包成功，SQLite原始SHA256仍为 `b18a5584590a07322c32fc0b59cb575b409beef60174fee28d8896ef5cf8cdaf`。保留 PulseAudio 外部 `/tmp` symlink 原文，目标临时数据不在归档内。完整 template ZIP 另有身份回执。恢复打包发现旧工具将原生刷新与ARC传输覆盖互斥，且未支持I14原生刷新；已向共同设施owner提交具体阻塞，尚未启动新writer。

## 当前等待条件（2026-10-02 11:14）

主线转达用户将 I13 Flash/GitHub 恢复列为第一优先级，并授权两项技能热修。cleaner不启动旧技能writer；等待技能会话 `01a0fa92-eb8e-7143-81fa-21eb002790f7` ready及共同恢复设施接线后，一次冻结新base。上下文binary保留不重编，完整原始现场已保存。WSL当前不可用，主线已核对development-2可用并统一准备glibc Runner；新prepare需独立冻结该endpoint/image实际身份，原operation不改。旧host adapter PGID54142仍SIGSTOP用于阻断cleanup，来源已停止、原卷与helper保留，尚未lab stop。

完整template ZIP为577,161,410 bytes / 63,825成员，SHA256 `abf6ae90c0fc3c8e1b63cca648847777400db808df7c919aa30304fd3b41c82f`。三份原生会话header/文件SHA与四个Git tree的HEAD/status另存 `source-native-identity.json` / `source-git-identity.json`。这些证据说明持久文件现场保全，不代表进程内存或外部`/tmp`数据恢复。

## 新材料冻结与通知边界（2026-10-02）

主线提供共同恢复接线身份后已核对：packager SHA256 `561cd17c87830804454e419ee02db64dd0d98d766e375f55dd38192154d3baf7`，恢复 main `0eb29b59e34f8dd1d8cb8f330b117519f7d5b8938ae9ce25299e31d082c26e03`，Linux prepare `135bd8fdde58afa0ec4cd8d83eb81d5b74d0898a621c7e33a6248f1c833d4026`。I14使用 `--continue-generation --refresh-native-materials --with-official-signal-evidence`，不传互斥的override参数，刷新后自动ARC保护。当前shared main及两技能整个目录已冻结为 `arc-cleaner-base-skills-ready.zip`，9个材料文件逐字核对，记录于 `base-skills-ready-identity.json`；沿用63fd context binary，四root prompt源码不改。此身份是冻结材料，不是实际部署或采用。

实际消费者由原DB核实：Issue1 OPEN的glm-1持有集成/检查职责，PR3 OPEN的glm-3实施；PR2已MERGED且glm-2 sleeping，review1已CLOSED/completed、结论成员glm-1。无需另造检查成员或唤醒已完成glm-2。Braid已有宿主 `--state <state> --external issue comment 1 --body-file <notice> --json` 接口；Issue1 owner自动收件，正文只@glm-3即可将同一通知送到PR3。正常评论记录投递与事件，实际turn input提供正文读取入口。正文仅包含两个技能名称、实际独立路径、新SKILL SHA与“继续当前工作前重新读取”的动作，无description或技能正文，无ACK要求和隐藏反馈。

现有shared main没有prepare通过后、首次dispatch前的一次通知接线，具体缺口及CLI方案已交主线整合；不直接SQL或改native历史。`skills-refresh-notice.md`与`skills-refresh-notification-plan.json`仅为待发送材料，不能当投递证据。通知需runtime-only，prepare-only保持原DB不变；发出后保留comment/delivery及实际input身份，重入先检查已有回执/评论避免重复。仍等待主线development-2 Runner实际镜像身份，未操作旧WSL/Console或其它source，未启动writer。

候选恢复包 `cleaner-resume-skills-ready.zip` 已成功装配并逐项核对，971,029,396 bytes，SHA256 `91118e8e9f084acac1e9ea564bc298a865729b57ea7433b36c4c05b5dfb2a16e`；manifest中的main、binary、nested完整workspace ZIP及9份技能文件均与实际字节一致。候选仍使用main `0eb29b59…`，不含待整合的一次恢复通知，不能作为最终部署包。独立计划为 `skills-refresh-recovery-plan.json`（稳定request_id、来源/Issue身份、实际消费者、路径/hash与通知文字），已交主线；原normal CLI方案保持，不临时改原DB/native。下一步等新通知接口hash及development-2 Runner身份后重新冻结最终恢复包，再prepare/launch与实际输入取证。

主线已提供development-2 Runner：image `sha256:3d51899c61e6464242a7545a1badb6445f368f4757828fd36f040c6954b56681`，endpoint `ssh://sfp7-ws.localhost`，daemon `e316f857-fe3d-4e7b-8236-9376f063fedc`，Linux/amd64、CPython3.12.3/glibc2.39，UID:GID501:20断网实际metadata执行成功。原件为 `runs/iteration14/development2-runner-20261002/`。private `target-runner-identity.json`及独立dev2 recipe/spec已冻结该身份、2GiB/2CPU/五槽，新operation为 `operation-dev2`；实际prepare/run须显式DOCKER_CONTEXT=development-2并核对实际daemon/image，不改旧operation。CLI comment无request-id参数；一次通知幂等需在稳定恢复计划与正常评论回执边界由shared owner实现，不能误用PR接口参数。当前等待shared新hash，尚未prepare/launch。

## 新职责入口要求

主线转达用户补充：work-item agent不必例行以“Let me start by reading the braid-collaboration skill and viewing the PR”开始。方法独立会话负责诊断例行维护、必要协作判断与已投影PR的重读边界，先方案，不改现场。本会话不重复方法调查、不改skills/role；保留当前强制重读notice为原候选，最终计划和role材料等职责入口方案明确后再冻结。通用一次通知接口仍由shared owner实现。原件、candidate和dev2spec/image保持不变，未prepare/launch。

共享一次通知接口已ready：packager SHA256 `7ea9f02fb02e1a36dcc86bb5356457097ed3bd75bbe1570e1341d975c89425f3`，main `a12ae58d81da57d9df5a736697a4f557ec3305c442f9aa9eea001925848952d5`，lab仍 `135bd8fd…`；新增 `--material-notice-plan <private JSON>`，等待实际prepare反馈后由owner提交。最终材料和通知仍等职责方法与用户已授权的技能What/Why方案，不使用旧“一律读两个技能”候选启动。原件、候选、dev2 image/spec保持，尚未prepare/launch。

## Console 恢复后的只读核对

用户确认WSL恢复后，只读核对原服务 `/home/yyh/.local/share/factory26/exp-console/20261002-review-sessions`：service `8cc80cad-d873-49ed-ab49-e958ba8852a3`、instance `8ccaaf92-02f0-4a60-904e-5564ba6957c3`、PID1676167 running、8765端口、7条registry；`/api/runs` HTTP200。旧cleaner仍指原container/volume及已停止的专属CLI accessor，`read_check=unavailable`，`/api/runtime` HTTP400保留具体“CLI访问容器需要运行且未暂停”。未启停Console或任何生成/accessor，不解除baseline暂停。读回为 `console-{runs,service,runtime-source}-readback.json`。

恢复后的新physical run仍按dev2冻结输入，不能因WSL恢复换回旧宿主。登记接口由现有唯一服务owner执行 `binary`/`register`，须HTTP停止后登记新的run身份及明确来源，不能覆盖旧ID。实际源码 `braid-console/docker_runtime.py:108`拒绝非unix://context；原服务位于WSL，new runtime位于另一dev2 daemon，所以直接live登记有明确跨宿主边界缺口，已报主线，不为此新建Console。`console-registration-handoff.json`保存实际接口和待填newrun/container/StartedAt/volume挂载/state/managed binary/accessor所有权等输入；当前未生成新物理身份，不能将模板当已登记。最终材料仍待职责方法方案，未prepare/launch。

## 已决定的职责入口与最终冻结条件

主线提交最小cleaner入口修复 `b13f4290`：两成员instructions以已有快照、需求与task材料进入工作，补充查询服务具体信息缺口、折叠、新变化或冲突；braid-collaboration按当前实际问题加载。SVC职责/MAIN_SKILLS/Braid/cleaner扩展保持。两instructions预期SHA256均为 `cc4765ccc58dfcf6823a164b8e598af2c05caa04a25901ad07b6b07bb7d3ab2d`，须进入最终fresh managed base。最终通知取消恢复后一律立即重读两主文件，只报告换版事实、技能名/path/hash，由角色本次判断消费；旧强制重读notice/计划作为原候选保留，不再用于launch。

What/Why技能正文仍由独立会话改写，本会话等待最终技能SHA。主线正在核对恢复后WSL容量，最后host选择尚未交付；已冻结dev2候选原样保留，不并行换宿主或启动prepare。Console跨宿主限制不自动授权新模块/第二实例。最终技能、成员instructions、通知接口与host决定均明确后，才一次冻结并执行唯一prepare。

## 收束交接

主线转达用户最新要求整理实验基础设施，并重新明确供应商配方与Harness能力边界、GLM5.3/Qwen方向。本会话立即停止新增freeze/prepare/launch及模型请求，不自行改模型或输入。停止到达前，最终fresh managed base和带正常一次换版notice的恢复package装配成功；最终skills/两成员instructions/shared main/binary/完整workspace/notice均可从制品manifest核对。`final-prepare.py`仅保存、未执行，其成功开关 `final-packaging-complete.json`未创建，`operation-wsl-return`未建立；没有在途offline准备、runtime或模型请求。通知没有发送，角色/技能的运行读取和判断采用未取得证据。

最终独立plan为 `final-material-notice-plan.json`，正文只报告技能换版name/path/hash、不要求统一复读；Wsl-return recipe/spec独立保留，旧spec、dev2候选及所有原件不改。实际artifact路径/SHA/bytes与包内身份见 `stopped-handoff.json`。先前容量只读门控记录远端55,826,632,704 bytes可用、预计额外峰值17,274,589,926 bytes、五槽占用3/可用2，来源同一container仍Stopped/Exit137/OOMKilled=false；这是当时门控，不代替未来启动核对。

Console最近只读核对仍是同一WSL服务、8765/7条登记；旧cleaner专属CLI accessor保持停止，HTTP200列表/具体runtime400保存。主线最后选择WSL与Console同宿主，dev2跨宿主限制仍保留作历史候选边界；未修改registry、新建实例或HTTP/collector。来源container/helper/volume、旧host adapter SIGSTOP现场与全部归档保留，无cleanup，dispatcher/baseline不解除暂停，其它run不操作。下一阶段需主线基于用户新方向明确后再推进，不活跃常驻等待。
