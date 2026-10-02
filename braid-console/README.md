# Factory26 Exp Console

Factory实验的薄接入入口，提供已登记运行的Home和Braid专用详情，属于实验基础设施，不依赖SVC或ARC，不进入参赛包。源码仍位于braid-console/，保留在Factory26父仓库中，没有独立Git仓库。Console拥有服务接入与显示状态；lab/冻结材料拥有实验事实，Braid CLI与归档拥有协作事实。

`web/`使用React、TypeScript、Vite、shadcn/ui、Tailwind CSS、Radix、Lucide与TanStack Query。App只管理Home、运行选择、React Router路径导航及离页保护；Home与runs.ts负责通用登记摘要，http.ts保留HTTP错误和响应。BraidRun负责工作项列表、详情、物理控制及其查询，Review负责PR下的冻结审阅与结论，Sessions负责会话导航，Transcript提供同源对话与Trace，FileBrowser提供工作区和origin阅读；Braid对象类型留在api.ts，不建立插件或adapter框架。
`server.py` 提供 HTTP 接口并服务构建后的前端。现场对象操作调用登记的 Braid CLI；归档浏览由 `archives.py` 读取保存的 SQLite 页面字段，不启动 CLI、worker 或原 Git。`docker_runtime.py` 只控制登记容器的物理暂停/恢复，并协调暂停时的 SQLite 写者锁；不修改业务数据或另建调度逻辑。Braid 继续拥有对象、Git及事件语义，不需要知道 Console、实验名或 ARC。

工作项详情的 Braid agent sessions 入口可查看对应 provider sessions 及历史。关系来自登记CLI的 `status --json.physical_sessions`；`group_id` 是持久Braid agent身份，provider恢复身份与native ID分别呈现。明确的 `replaced/retired` 标为历史，其他状态保留CLI原始生命周期，不推断当前归属；实际暂停/运行状态看上方生成状态。CLI按physical目录枚举，缺失physical材料的会话可能未列出，空结果不表示从未启动。

PR 详情保留 `review_requests` 中的审阅入口，包括已完成请求与已合并 PR。Review 页面调用登记 CLI 的 `pr review view`，分别显示当前执行责任、冻结候选、checkout、实际结论作者及不可变结论；当前适用性变化直接呈现 CLI 的 freshness errors，不改写历史 Approved。审阅会话按 `work_item_kind=review` 和请求编号匹配；结论或 checkout 明确指向 Issue agent 时另给原 Issue 会话入口，不将其全部对话冒记为本次审阅。归档审阅详情尚未接入，具体读取错误保留，不从评论拼造审阅记录。详情接口为 `GET /api/review?run=<ID>&pr=<PR编号>&id=<审阅编号>`，PR 归属由 Braid 核对。

Provider详情默认以对话阅读原生输入与Agent正文，工具、思考和后台通知折叠为过程活动，具体错误直接可见。原生user标为“输入”，不推断来自人类；工具按全部已加载记录中的唯一call ID配对，跨父链不连续、压缩或分支摘要停止配对，返回仅表示“已返回”。每条正文、调用和结果可定位到同源Trace的字节位置；切换保留阅读位置，Trace保留全部原生事件与完整脱敏JSON。历史仍从开头分批加载、手动刷新，已加载末条不代表最新进展。身份材料与turn历史按需展开。

`native_sessions.py`只从CLI返回的路径读取，在固定Docker访问容器或本机运行中执行只读JSONL读取；浏览器仅提交physical记录ID和字节偏移。读取核对文件header的native ID，每批最多50条、约1MiB，保留完整行与稳定字节游标；单行超过8MiB明确报告边界，末尾未完整行等下次读取。工具大文本可滚动查看，完整原生记录可展开；图片等非文本内容呈原生JSON。凭据字段、Bearer、常见key格式与读取环境中凭据值脱敏。原生日志缺失或身份不匹配单独报错，会话元数据保留，服务不重建历史文件。

当前支持Pi与Codex JSONL header身份核对及原生记录展示；已在I12真实Pi会话验收，Codex尚未实测。服务不接受自由cli_command；原生读取使用固定Docker配置或受管理本机运行。关系与正文接口分别为 `GET /api/sessions?run=<ID>`、`GET /api/transcript?run=<ID>&provider=<physical记录ID>&offset=<字节位置>`。

Agent和Provider页的“文件”可浏览CLI登记worktree的当前文件，包含未提交、未跟踪和`.braid`材料；多个不同目录须明确选择。改派可沿用同一目录，因此历史会话路径不是历史快照，也不证明当前归属。读取时间随目录、正文分别显示，刷新不暂停生成或建立完整快照。

“origin分支”以及运行页的“浏览origin代码”读取本次运行`state/origin.git`共享裸库的`refs/heads/*`。选择分支固定完整commit，目录、文件及缓存始终绑定该commit；刷新列表保留版本，显式“更新到分支最新”才切换。运行级阅读弹窗保留下面工作项的草稿。origin只包含已push的代码，空树不能替换为Agent当前工作区。

`code_files.py`在登记CLI同一namespace执行固定只读reader。`GET /api/code/refs?run=<ID>`列分支，`GET /api/code?run=<ID>&source=workspace&provider=<physical记录ID>&path=<相对路径>`读取登记目录；origin读取改传`source=origin&commit=<完整SHA>`。浏览器不能指定绝对根路径。读取核对实际容器及嵌套挂载来源，拒绝`.git`、越界与符号链接穿越；符号链接和子模块仅展示保存的目标或身份。特殊文件不读取，目录超过2000项或文件超过1MiB明确报错，不静默截断；二进制及非UTF-8内容说明不可预览。代码及HTML作为文本，Markdown沿用安全预览，凭据复用原生reader的脱敏规则。

origin读取使用`for-each-ref`、`ls-tree -z`和`cat-file`，读取前明确拒绝partial clone/promisor配置和对象标记，保留禁用lazy fetch的环境保护，不执行checkout、fetch、clone、filters或Braid工作树恢复校验。当前代码阅读只接入live来源；归档文件入口直接说明缺少origin和会话工作区映射，不读取原绝对目录、重建仓库或拿最终应用代替分支历史。

页面使用React Router显式路径：`/`、`/runs/:run`、`/runs/:run/issues/:id`或`prs/:id`，PR 审阅为`/runs/:run/prs/:id/reviews/:review`；工作项或审阅的会话层级追加`/agents/:agent/providers/:provider`。页面身份只来自路径，不解析旧`?run&kind&id&agent&provider`，也不重定向旧链接；查询参数不承担页面身份。有效深链直接打开及刷新由Python返回前端入口，缺失资源、未知API和不合法页面路径保留404。离开工作项时，未提交草稿保护同时作用于点击和浏览器历史导航，取消切换保留原URL与草稿；操作中阻止切换。

## 首页与运行事实

根路径始终打开Home，零登记明确显示空状态和管理CLI方法；不会自动选首项或渲染工作项加载骨架。未登记run保留链接身份并提供返回Home，不转向别的现场。选择Braid项才发起对象及运行状态读取；品牌和首页按钮与原深链、前后导航一起经过草稿保护。

Home展示登记的live/archive、人工写入许可和是否登记暂停/恢复。许可不表示此刻可执行：现场状态在Braid详情由实际CLI/Docker读取，具体失败保留；首页不批量查询所有现场。归档显示启动核对所得保存对象范围和native等缺口，不能据此声称完整历史。

运行事实只读取生产者JSON记录的variant、experiment_name、status和updated_at。归档使用其标准run.json；现场可用显式绝对路径run_record登记来源。页面保留来源路径、SHA-256、缺失/解析错误；没有实验名就显示未知，不猜目录、不从Issue关闭推导实验完成。记录中的status是保存时事实，不表示当前进程或任务终态。Console不启动实验、不管理重试、预算或调度，当前只支持Braid接入。

## 稳定服务与接入

先在 `web/` 执行 `pnpm install --frozen-lockfile` 与 `pnpm build`。长期服务放在实验 `runs/`、`prepared/` 和 `.factory26/` 之外，例如宿主 `~/.local/share/factory26/exp-console/<部署名>/`；不要直接从实验目录启动长期服务。

```sh
python3 braid-console/service.py prepare --destination /absolute/stable/exp-console/deployment \
  --registry /absolute/console-input.json --python /absolute/stable/python3
python3 braid-console/service.py serve --service /absolute/stable/exp-console/deployment --port 8765
```

本轮服务接口hard cutoff：只接受 `factory26.exp-console-service` schema1 manifest，不读取旧Console服务格式或自由registry/journal启动参数。`prepare`只向新目录的app/复制Python源码和已构建前端，记录每个文件身份、实际 Python 路径、版本及 prefix，不安装到已有服务，不复制实验 workspace。Python 至少为3.11，不能来自 attempt-local 环境。本次开发只读核对可以用 `--development-output` 在新输出目录准备制品；它不是长期部署或历史迁移。`serve` 用登记解释器执行冻结程序，监听127.0.0.1；本机只读或人工操作不需要Node。

服务根固定app/、manifest.json、active.json、logs/与console-actions.jsonl；live接入按需创建binaries/，退役前序证据单独放history/，没有current指针、stage/activate/rollback或永久兼容层。manifest.json同时是接入配置、制品回执和现有GC可见的依赖记录。HTTP运行身份保存在 `active.json`，服务锁阻止并行HTTP实例与配置修改。`logs/http.log` 每份最多5MiB、保留3份备份；异常与访问记录共用轮转。`console-actions.jsonl` 保留人工操作及接入管理的 started/completed/unconfirmed 回执，继续追加、flush/fsync，不跟访问日志自动淘汰。stdout只打印启动入口，部署操作方保存进程或终端身份。

输入registry是运行列表，每项明确 `mode`。例如只读历史归档：

```json
[
  {"id":"saved-github-20260930","label":"GitHub 保存状态","mode":"archive",
   "writable":false,"archive":"/absolute/archive/evidence"}
]
```

归档必须有 `braid-state/braid.sqlite3`。Console以 `mode=ro&immutable=1` 连接，不创建或修改WAL/SHM；非空WAL明确拒绝，交由生产者保存冻结数据库。对象投影限定已保存的标题、正文、revision、状态、成员、讨论及父子/关联关系，不重新计算Git、合并条件或调度事实。按实际表字段判断支持能力；旧schema缺失的关系与成员字段明确提示，空值不证明当时不存在。归档API强制拒绝修改和物理控制，页面显示“保存状态只读”。

会话目录优先用保存的 `braid-state/sessions.json`，缺失才读取 `status.json.physical_sessions`；两者冲突时展示缺口，不静默合并。原文只通过 `native/manifest.json` 的唯一provider/group/session及工作项、原路径身份匹配，限定归档native目录相对路径并核对SHA-256和header。原绝对路径只作历史事实，不回退旧workspace或容器。缺manifest、文件或不支持的身份保留会话元数据和具体错误；不会重建日志，也不把可读目录说成完整历史。当前Pi已有真实归档接口反馈；其它provider未实测。

现场输入另含 `state`、原执行根 `workspace`、可执行 `binary` 和明确 `writable`。`binary` 会复制到服务管理的 `binaries/<sha256>/braid`，运行接入引用此副本；保留原workspace是现场CLI/Git继续使用原路径空间的必要条件。配置例如：

```json
{"id":"current-run","label":"当前现场","mode":"live","writable":true,
 "state":"/absolute/workspace/.factory26/run/braid-state",
 "workspace":"/absolute/workspace","binary":"/absolute/frozen/braid"}
```

先准备空列表 `[]` 可以取得服务ID，再用 `binary --service <目录> --source <冻结binary>` 准备稳定binary。创建确实需要的Console自有访问容器后，使用 `register --service <目录> --registry <新增运行列表>` 登记实际完整身份。管理命令与服务制品保持配套，部署后使用 `<服务目录>/app/service.py`；执行时HTTP必须已停止。运行ID不能覆盖原接入或重新指向另一现场，以免旧草稿写错对象。

停止前台HTTP用对应终端Ctrl-C或对其已确认PID发送SIGTERM；服务只关闭自己的HTTP并记录终态，不停止SSH转发、访问容器或生成容器。WSL部署的转发仍由操作方以独立SSH进程管理，`ssh -N -L 8765:127.0.0.1:8765 wsl.win-ws.localhost` 只是转发入口，不代表服务或生成已启动。

即使HTTP已停，manifest中可恢复的配置仍保护服务、Python、现场整个workspace、所有宿主挂载及归档。GC扫描须包含稳定服务根；未扫描的服务或旧式registry必须显式 `--protect`。本轮只支持只读plan，不因此授权回收。

显式停止接入时，先分别关闭转发与HTTP；Docker接入还须确认Console自有访问容器已停止，再执行 `release --service <目录> --run <ID> --confirm-no-forward`。它从当前配置移除此接入并保存原配置及确认回执；HTTP停止、容器查不到或未知daemon都不算解除引用。原配置只保留为journal中的来源事实，重新接入需要重新登记和核对依赖；服务目录及Python仍由服务配置保护。未停止的其它消费者由各自运行记录继续保护。此命令不删除文件、容器或生成现场。

服务切换需要明确部署操作：先从实际登记输入准备有效新根，再核对并停止旧HTTP及自动启动入口，保存旧配置、active/launch和journal身份到新根history；旧manifest.json原子改名为retired-service.json并记录退役，新manifest成为唯一权威配置。历史journal不混入新活动journal，旧冻结程序和实验数据不删除。新服务失败保留当前配置及具体错误，继续修新服务，不自动恢复旧服务。GC遇到仍有权威manifest的旧格式会失败关闭；历史配置本身不作为可恢复接入重新保护现场。

Braid状态里的Git与工作树路径属于生成时的执行环境。运行在容器中时，稳定接入的宿主`state`、`workspace`保存实际执行根；服务只接受受管理本机CLI或固定Docker配置，不支持自由cli_command。若需要暂停生成后继续人工访问，先为每个运行创建一个独立CLI访问容器：

```sh
docker run -d --init --name <访问容器名称> --label factory26.console.run=<运行ID> \
  --label factory26.console.service=<稳定服务ID> \
  --mount type=bind,source=<受管理binary>,target=/console/braid,readonly \
  --mount type=bind,source=<原工作区在宿主的实际根>,target=<原容器工作区路径> \
  --network none \
  --user <原容器用户> --workdir <原容器工作目录> \
  --entrypoint sleep <原容器image完整ID> infinity
```

登记固定Docker配置后，服务通过该访问容器执行受管理binary的对象CLI；不接受浏览器或registry提供自由命令。

原容器ID、image ID、用户、工作目录和挂载须从实际运行核对；binary及state必须位于共享挂载中，并在访问容器里保留原绝对路径。显式挂载实际工作区，不复制数据库或继承原容器的环境变量；有其它执行所需挂载时一并按实际来源登记。固定image并覆盖entrypoint只运行`sleep`待命，`--init`使停止信号能结束待命进程，`--network none`隔离网络。对象CLI不启动Braid worker，也不恢复原生成容器；人工评论仍按原生事务入队，待用户恢复后由原runtime消费。复用访问容器避免每次浏览器轮询都创建和移除容器。

生成使用Docker named volume的`volume-subpath`时，`Mounts.Source`是volume根，实际工作区为该根加上`HostConfig.Mounts`中同一volume、目标目录的`VolumeOptions.Subpath`。上例的工作区挂载须改为`--mount type=volume,source=<原volume名称>,target=<原容器工作区路径>,volume-subpath=<原stage子目录>`，使用同一named volume及子目录。不能只用volume根或假定`--volumes-from`保留子目录；只bind宿主子目录也不会建立Docker的volume消费者引用。Console的共享路径核对采用同一换算，并继续核对最长嵌套挂载。Docker接入的宿主state/workspace保存精确映射供GC引用，存在性在固定访问容器内核实；原生Console用户不需要遍历Docker宿主数据目录，也不需要root权限。本机接入仍直接核实宿主目录，受管理binary的宿主身份检查保持。

访问容器由Console接入管理命令 `access-start/access-stop --service <目录> --run <ID>` 显式启停，不设置自动重启。命令先核对固定context、完整ID、service/run所有权标签和真实挂载；不操作借用或未知容器，不自动重建。停止HTTP不停止访问容器，停止访问容器也不解除可恢复配置的引用。移除容器须由操作方在解除接入、核对所有权后另行执行。named volume在访问容器停止后仍被引用；最终清理顺序为关闭转发和HTTP、停止访问容器、release接入、明确移除该访问容器，再执行实验资源清理。生成结束及原runtime被移除后，访问容器仍可保留读取材料，但原runtime控制不再可用。生成容器属于实验，只接受既有明确pause/resume操作，不归Console清理。

需要页面暂停/恢复控制时，在同一run中登记下面的`docker`配置，替换其中的完整容器ID及实际路径，不同时设置`cli_command`：

```json
"docker": {
  "runtime_container": "<生成容器完整64位ID>",
  "cli_container": "<访问容器完整64位ID>",
  "context": "<本宿主固定Docker context>",
  "binary": "/console/braid",
  "mounts": [{"source":"/absolute/workspace","destination":"/workspace"}],
  "state": "/workspace/template/.factory26/<实际Braid运行ID>/braid-state"
}
```

受管理配置中的宿主binary已冻结到服务目录，并须挂载到docker.binary；原workspace及其其它宿主挂载在mounts中完整列出。容器state经最长匹配挂载映射后必须等于登记宿主state。当前受管理Docker只支持本宿主Unix socket context，远端路径映射尚不支持。`docker`描述执行路径空间。服务据此生成上述对象CLI命令，物理控制只作用于生成容器，不能登记同一个容器兼任两者。配置不依赖容器名称或实验命名；浏览器不能提交容器ID、路径或执行命令。

页面对当前选中run显示实际生成状态。暂停冻结该容器内全部Agent会话、子进程和Braid定期检查，人工查看和输入仍通过访问容器处理。恢复需要用户点击并确认，会继续原运行及已入队人工输入；停止或丢失的生成容器不能由此启动或重建。控制状态查询失败时显示未确认状态，对象查询保持独立；重启Console本身不暂停或恢复生成。

新暂停先核对两容器共享同一数据库挂载，再在Linux访问容器中使用现存WAL数据库的`BEGIN IMMEDIATE`取得写者锁；持锁暂停并确认生成容器实际`Paused`，随后`ROLLBACK`释放。门闩不修改数据行，取得失败时不发新暂停命令。访问镜像需具备Python3及sqlite3标准库，数据库挂载可写；锁不能由另一内核的宿主文件连接替代。每run的物理控制与Console修改串行执行，普通读取无需等待此操作锁。

对已经暂停的运行，请求`pause`只核对并释放写者锁，不解除或重新施加暂停。直接Docker暂停如果冻住了现存写事务，该核对会保留具体SQLite错误；不能通过清理锁文件、复制state或自动unpause修复。写者锁可取得不等于评论或编辑业务已验收，物理暂停也不等于应用已经形成完整恢复检查点。

运行状态接口为`GET /api/runtime?run=<run ID>`，控制接口为`POST /api/control`，JSON正文仅需`{"run":"<run ID>","action":"pause"}`或`resume`。控制与对象修改共用journal，保存固定容器身份及started/completed/failed/unconfirmed回执。Docker超时不能被当作请求已取消；结果未确认时先读取实际状态并查journal，不自动重试或执行恢复补偿。

服务只在基础命令后追加既有对象操作，不改变数据库里的路径，也不在失败后偷偷换到其它副本。对原生成容器执行`docker exec`会被其暂停状态阻止；需要暂停后继续访问时，应执行在上述独立访问容器中。

读接口使用原生Issue/PR及comment JSON；写接口通过 `--external` 执行编辑、评论、回复、隐藏、解决、关闭与重开。
正文编辑保留观察到的revision，发现已改变时要求刷新；CLI没有原子的revision前提，提交瞬间的并发编辑仍需人工核对。
讨论resolve作用于整条thread，局部整理使用hide及原因。隐藏与已解决历史按需展开，后续新回复保留可见性。

每次修改在独立journal保存原始输入和实际CLI回执。CLI写入失败或超时不自动重试；先核对真实对象与journal。
消息入队、负责人读取和业务完成是不同事实，界面不根据CLI成功推断Agent已经采用指示。
当前运行的身份、资源、暂停与实验条件归对应task packet，不写在通用页面协议中。
