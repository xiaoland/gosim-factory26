# Factory26 Exp Console 首页与服务切换

2026-10-01。用户已授权本批架构收口、实施、部署与限定提交，原话及范围见同目录 packet。本轮沿用现有 Console 服务和真实保存归档，不恢复 I12 或 WSL，不发送业务写入。

## 职责与决定

Home 是 Factory 实验接入入口，只列出已登记运行与来源明确的材料事实。实验的 variant、保存时状态等来自生产者 run.json；缺少实验名时显示未知，不猜目录或从协作对象终态推导实验完成。登记的写入许可、Docker 控制配置与当前现场能否操作分别表达；首页不批量执行各 run 的 CLI 或 Docker。归档核对只证明已保存字段可供阅读，不能代表全历史完整。

App 只持有 Home、运行选择、导航和离页保护；Home 与通用运行摘要、HTTP 读取独立于 Braid 对象类型。BraidRun 收纳原工作项列表、Detail、运行控制与它们的查询，Sessions 保持 Braid 专用。继续使用已有 query 深链和 history 管理，不引入路由依赖、adapter 框架或无理由搬目录。无 run 时保持 Home；未登记 run 显示原链接身份与返回入口，不能暗中选择首项。选择 Braid 后才读取对象和物理状态。

用户随后明确修正：“不必保留原服务目录，甚至可以进一步改进服务目录等，建立一个干净的架构、实现，做hard cutoff”。这撤销了保留服务根、旧身份和升级兼容的前提。Advisor按新前提独立复核后，最终采用新稳定根和服务ID，固定app目录、单一 `factory26.exp-console-service` schema1 manifest；去掉 stage/activate/rollback、双schema读取、程序选择、旧server自由registry/journal入口。仓库目录名仍为braid-console，通用入口和Braid详情已在模块边界分开，无须仅为改名搬目录。

新根按明确部署名放在 `~/.local/share/factory26/exp-console/<部署名>/`，app/冻结源码和前端，manifest拥有配置与版本身份，active/launch记录HTTP，logs有界轮转，console-actions.jsonl是本服务活动journal，binaries仅按实际live接入建立，history保留前一服务的配置和操作记录来源。两份归档通过显式输入重新登记，run ID沿用数据接入名称，新service ID与旧部署明确区分；没有自动迁移、版本回退或current指针。

先准备有效新manifest，核对程序、Python与归档依赖；再核实并停止旧HTTP，确认退出和锁释放，保存旧manifest/active/launch及实际存在的journal并核对身份。旧根manifest原子改名为retired-service.json，另存退役回执；旧启动命令因此缺少权威配置。启动新HTTP并读取真实API后交付新入口。短暂的两份依赖保护是准备阶段的保守重叠，最终只有新manifest是GC权威。旧配置和journal是history中的证据，不重新登记或混入新活动journal。

服务切换不删除实验归档、native、数据库、Git或无关文件，不改变旧冻结源码；新服务启动失败时保留registered配置保护并继续修新服务，不自动恢复旧程序。GC只解析新格式；其它仍叫manifest.json的旧Console配置使plan失败关闭，不能静默忽略其引用。本批不操作SSH、访问容器、生成容器或WSL，不设置登录自启或自动恢复。

单项现场资源错误归该 run，禁止该项 CLI/控制；服务的程序与 Python 完整性仍是全局硬门禁。此隔离不能省略 binary 身份校验，也不能让有错误的 run 继续执行。

## 验收边界

反馈来自 Python/TypeScript 编译、前端构建、实际空登记服务、两份真实归档 HTTP/API 和最终稳定服务。保留 Home、零 run、未知 run、对象与会话深链、返回及历史导航的观察；草稿保护只有可用浏览器与真实可写现场才可实测，本轮不为验收建立现场或发送评论。浏览器若仍被管理 policy 拒绝，明确未验，不换通道绕过。不写或跑 Factory/Braid/SVC 测试、mock、fixture、probe 或自检。

起点及后续原始回执：`runs/braid-console-control/20261001-exp-console-home/`。起点保存31个限定文件、diff、完整Git状态和稳定服务 manifest/active/launch 身份；TDD已有 assignee dirty、I12历史更新及其它协作修改不属于本批。

## 实际结果与当前服务

实现与部署已完成。最终入口为 http://127.0.0.1:8765/，新稳定根 `/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-home`，service ID `f5319ab4-537d-4cc4-9b21-26b911a859b8`。HTTP PID84660、instance `a16c5311-bb70-4120-8bfe-324b93924dcf`，启动2026-10-01T02:31:44Z；启动命令所在终端结束后独立读取确认PPID1及服务持续可用。未设置登录自启、自动恢复或SSH转发。服务app源码与前端的文件身份在manifest中；两个run仅为只读归档，没有现场控制。

旧PID75619与其active、完整命令及09:01:08启动时刻一致，已SIGTERM停止并确认进程退出和原锁可取得。原manifest原子改名为retired-service.json，原冻结program未修改。旧配置、结束active、launch及退役回执保存在新服务history/console-20261001-55fe50a，复制SHA一致；原console-actions.jsonl实际不存在，回执明确记录缺失，没有伪造或接续journal。旧目录不再有权威manifest，新根成为唯一服务接入配置；没有删除实验、native、DB、Git或旧程序。

Python六个Console模块及lab/gc编译通过，TypeScript/Vite构建通过；保留原约1.25MB主bundle警告，未加入依赖或构建优化范围。最终冻结制品的真实空登记实例返回200 []，浏览器显示明确空状态/管理CLI而非工作项骨架；无效run接口400与页面原身份保留，返回根Home和back/forward实际通过。空实例使用与部署完全相同的artifact_files，核对后显式停止、配置退役，未留下额外服务进程。早先取消的schema2空制品仅作过程证据，也已停止和退役，没有执行stage/activate。

最终服务两份归档的列表、根Issue与sessions均200，分别1/23个对象和1/215条会话。Pi transcript200，浏览器加载21个可呈现原文entry（接口首批24条），会话/provider深链刷新、返回Home及back/forward保持身份；GitHub PR#2及其provider历史实际可读，正文保持HTTP400 native manifest唯一映射缺失与不回退旧路径的具体错误。两份归档的DB、native、run.json、WAL/SHM存在性及身份前后完全一致。Home的GitHub记录仍显示生产者保存status=generating，虽根Issue已CLOSED也不据此改成实验完成。

针对新服务根和本次退役旧服务根的只读GC plan complete=true，只有新manifest的6条保护引用，零错误、零候选；没有扫描历史运行域、GC apply或删除。新服务未启动时的plan同样保持6条引用，说明HTTP是否运行不解除可恢复配置。history随新服务根保留，但其中旧配置只作证据，不重新pin旧依赖。

草稿保护保留原Detail函数体和navigation守卫；本轮没有可写现场，确认/取消、beforeunload及真实业务写入未验，不将只读导航或源码保留当作写入验收。live资源故障隔离、Docker控制、Codex原文和日志阈值轮转也未实测，明确保留边界。当前不需要恢复I12或WSL才能使用已登记归档。

原始反馈入口：frontend-build-final.log、new-service-prepared.json、retirement.json、process-final.json、http-final.json、empty-http-final.json、browser-final.json、archive-files.before/after.json、gc-prepared/final.json与validation-final.json，均在本批runs目录。起点快照和限定源码增量继续保留，提交不纳入TDD assignee、I12历史行及其它dirty。
