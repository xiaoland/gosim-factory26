# I13-2 官网 Flash/GitHub 内存修复热恢复

本会话获授权取消当前资源等待来源，并在有证据的共用 Braid 内存修复编译成功、主会话交接后执行一次官网接续。来源 run `e1aa595f6995`、submission `8fad2a412927`、逻辑 Braid run `20261001-052115-e45f4278`，冻结原包 SHA256 为 `bd897c86b9dbb56186d3929522e01d2dff19d76fb940f1b613e00ee80751f615`。新原件、准备与 journal 独占 `runs/iteration13/i13-2-20261001/hosted-github-memory-r3/`；不修改全局 packet、本地运行、I14 或 Console。

用户授权由主会话转交：“用户已授权取消当前卡住来源并独立官网恢复收集证据”；修复完成后无需等待未知 OOM 根因，可以实际运行收证据。原模型根 GLM-5.3-Flash、advisor Kimi-K2.7-Code，全部使用自有 ARC API key；`billing_mode=self_funded`、`allow_competition_credit=false`，不使用比赛额度、不增加其它尝试。来源写请求 pending 时只读核查，不重复发送。

当前实施先以原 journal 与实际 GET 核对来源，唯一取消写请求的 pending 与原 HTTP 响应保存在 `source-stop/`。停止终态独立读回后，再只读下载最终 workspace ZIP。没有可确认的原子早期检查点，不回滚到单独 Git/DB，不删除约一万五千条资源拒绝历史；原 Git、未提交文件、SQLite/WAL、原生记录全部保全。官网 ZIP 如遗漏 clone 私有 Git，仅依据逐 clone 发布 ref 与原生证据重建管理信息，不能以数据库 branch 覆盖文件；原暂存区、reflog、未发布提交与 merge 状态缺失必须如实记录。

后续复用 `package_completed_recovery --continue-generation`，指定新 Linux binary、源码与身份回执，并启用 `--with-official-signal-evidence`。先执行无网络、无模型的 Linux prepare-only 与独立 readback，通过后用 operation prepare/run 执行唯一 snapshot/create/start，并接入原 PID245 所属的唯一官网 collector，保留 Sheet/GitHub scheduler 历史。验收来自编译、实际操作及已授权运行，不运行 Factory/Braid 测试、smoke 或 probe。

## 来源停止与检查点证据

2026-10-02 10:02:37 CST，唯一取消 POST 返回 HTTP200/curl0；10:03:02 独立 GET 读回 CANCELLED，run/submission 与原 journal 一致、pending=false。首份最终 ZIP 下载在 HTTP200 下发生 curl92 HTTP/2 中断，188240016字节半成品及错误保留在 `source-stop/`；只读 HTTP/1.1 重试于10:06:43完成，原件为 `source-download-r2/workspace.zip`，313573403字节，SHA256 `beda01ec104caeeebb8728299f7c2ae9ff3fe7e9341705b71dfe418792559a82`。没有重发取消或收费请求。

原 ZIP 有47874个成员，clone私有 `.git` 全部缺失；当前十份 native session 与01:52Z已有采集逐字相同。来源 Git origin 与 native 保全在 `source-facts/`，独立比较和逐行Git见证分别为 `clone-tree-comparison.json`、`git-native-witnesses.json`；重建输入是私有根目录的 `git-reconstruction.json`。应用空seed为e9e24e0，根clone为base-scaffolding@828d17e（八个tracked文件全部吻合）；PR2 ddfbe6a、PR3 29e8a6e、PR5 78c40c0、PR6 951e9ba tracked文件均吻合。PR4原clone为89c4a3d，有八个tracked修改及二十个额外文件，其部分合并原件完整保留。最新origin/pr4为44669c4，是根在 `/tmp/pr4-takeover` 完成合并与修正后发布；不能以该ref覆盖原clone，也不能假称原clone的staging/MERGE_HEAD已恢复。

没有可确认的错误扩散前原子检查点，本次接续取消时完整可取得现场；不会删除资源拒绝历史或单独回滚Git/SQLite。停止终态为平台执行停止证据，ZIP本身没有嵌入官网run身份，其来源关联依据此次下载endpoint与保存的journal/status。

## 修复制品与准备

主会话 `linux-fix/handoff.json` 状态ready，Linux编译回执completed/exit0。新binary SHA256 `e209d754d89fe1d972ab0acbda020356e56121501b0756183d88857be7e03d22`；源码集合 `db590aefd9d6ac308aeb576b31182acb9e4b8c8039e1dde76a18079609f203c7`，源码tar SHA256 `cf454ada449e44c324f6eedcae438ae0d5ff4b253eb0089e91f0f865902c4baf`。公共agent_support SHA256 `66b3e6d647cb7708d114d6521e3a0d7eceac94a39e8eb7ffa28d5ba403fce2b7`，已核对交接身份。

`operation-spec.json` 冻结单项授权、self_funded/比赛额度关闭与既有monitor输出目录，operation prepare正在执行真实无网络Linux准备。包纳入共用claim前资源就绪检查、快照排序内存改进、native managed_state实际回执/capture内存，以及存活进程优先的RSS/PSS/Anon/File/Shmem/I/O/fd采集；不改变压力阈值。准备成功、原生实际继续和新增字段实际取得分别报告，不能以打包代替运行验收。

## 首次准备失败及有界修正

首项 operation 的恢复包已经冻结为 `ce504eb6edf0bbaa8ad672bb7df9e82e7964fe39cba97ed4cb4d1a25cf580a8a`（708669139字节），binary/helper/来源ZIP与handoff逐项一致，资源helper与managed原生模块齐备。实际container-prepare在Linux编译镜像中运行，入口verify_package明确报错“参赛包需要 Linux x86_64、CPython 3.12”，exit1；它在恢复之前停止，尚未启动Braid/模型。这是本次镜像选择错误，不是恢复源码或新OOM。实际隔离容器 `7af7994eb055d142f6e61c4276b6c1added828b5e8cd3484216ba5487f3cfdb1` 与全部文件保留；随后组件停止sleep容器，OOMKilled=false，其ExitCode137不作为生成OOM证据。

原 operation/spec/readback/logs 不覆盖；`operation-spec-r2.json` 直接引用已冻结的同一ZIP，仅将准备镜像改为此前官网r2实际成功使用的 `sha256:a2d86e7815bcfe5d6f1da6414ad03b4c31f2cfaed070c80be2479a9027d47c8e`。第二项operation-r2正在独占无网络容器 `fe6971329e9c19718d7e506d2b955902e677354e28d254ba1437eefa8fc9ae6a` 中实际准备。仅重做无模型准备，没有新snapshot/create/start，没有修改来源或派生包字节。

## 单一采集器接收前提

旧PID245已自然退出，按Darwin进程出生身份读取为lost；现有scheduler.done包含Sheet `f16834f58674` 与旧GitHub `e1aa595f6995`。没有人为终止采集进程，没有第二个采集器。scheduler与legacy-monitor-launch原件保存在 `collector-handoff/`，同一monitor目录的动态targets已登记旧两项实际journal/run/submission身份，新operation启动后只追加新项并接收；旧next/liveness/notifications/done全部保留。当前尚未启动新collector或模型。

## 实际准备通过与控制层阻塞

第二次实际入口stdout已经确认“prepared without starting Braid”，`readback.json` 真实保存exit0；974份保留文件无差异，七表数据库、工作树路径、profiles/root保持，实际binary与e209d754 SHA一致，git_errors/material_mismatches为空。通过已知容器宿主PID1648134的 `/proc/<PID>/root/evidence/` 独立SSH读回，原文与所选字段分别保存在 `prepare-r2-host-independent-readback.json`、`prepared-readback-observation.json`；这项证据不由静态实现阅读推断，没有模型启动。

组件尚未发布canonical准备回执。宿主SSH的uptime/进程读取可成功，但同宿主Docker inspect在20秒内无stdout/stderr超时，多个Docker exec也不返回；原操作仍等待Docker响应/回传。相关只读诊断保存在 `prepare-r2-host-docker-readback.json`、`host-docker-process.json`，已向主会话升级共享控制层问题。没有重启Docker、停止其它运行、重复prepare或绕过成功回执门控，也没有发新官网收费写请求。

## 输运失败的精确结论与共享归属

canonical operation-r2已取得实际失败回执：失败发生在恢复和独立readback成功之后，`docker cp <container>:/workspace/template/. prepared-workspace` 的全工作区额外回传600秒超时；本地 `/evidence` 独立原件全部保留。组件随后停止同一容器，Running=false/Pid0/OOMKilled=false。这不是新生成失败或新的OOM，亦不应将之前Docker CLI等待解释为整台daemon损坏；直接Unix socket容器JSON与/_ping实际可返回，问题目前集中在I/O/大传输。

主会话明确共享 `lab/arc_bench/recovery.py` 由本地恢复worker持有，其压缩tar stdout输运改动SHA256为 `10658681127d8998de2efb2fead4c526dc5ecafc20323593985dd014feea1028`；本会话只读该文件。一次拟议patch因源码已更新而原子校验失败，没有应用源码改动。已向主会话交接最小接口：原spec/input hashes不变，保全failed receipt和部分副本，在已停止的同一容器完成全量压缩输运，以已有成功execution/readback与verify_launch确认派生prepared回执，不创建新容器、不重跑main或模型。此接口与实际接续由共享owner负责，官网私有流程在接续完成后继续唯一启动。

本次实际 `package-recovery-resource-environment.json` 读回enabled=true，resource helper与native-managed模块均存在，FACTORY_RESOURCE_HELPER/DIR/NATIVE_RUNTIME_MODULE均已准备；这证明资源治理接线已启用，仍不等于模型实际运行或新OOM字段已经被采到。

## 同一停止现场的完整导出

停止后的同一容器通过只读 `docker cp ... - | gzip -1` 完成全量导出，未重启容器或调用main/模型。原件位于私有目录 `stopped-attempt-export/workspace.tar.gz`，331030054字节，SHA256 `cab38f64135d29936ac907df5182d0ee170ce9fd5294b171546262a6fdb83b49`，输运591.41秒、exit0。使用现有 `extract_output` 解析后，974份保留文件逐项核对无差异；`validation.json` 与原输运receipt/stderr均保全。

用户通过主会话明确恢复Flash/GitHub为第一优先级。共享owner负责提供消费已有完整export、实际prepare/readback及停止/隔离证据的安全reentry；本会话保持recovery.py只读，不覆盖旧failed/partial原件，不重复不可用WSL的输运、不重跑main。接口交接后独立verify_launch全部门控，通过后按原Flash/K2.7-Code/ARC/self_funded、比赛额度false执行唯一官网接续；收费请求pending时仅只读核对。

## Reentry门控与唯一启动

共享owner交接的recovery.py SHA256为 `135bd8fdde58afa0ec4cd8d83eb81d5b74d0898a621c7e33a6248f1c833d4026`。实际 `--complete-prepared-transport` 成功发布prepared回执，完整tar和解压内容逐项核对、原spec/input/package/runner与停止隔离证据均通过；保留旧failed receipt和partial工作区。随后原operation-r2 prepare实际完成冻结，未调用Docker或重跑main。

独立verify_inputs、verify_launch和operation launch_gate均通过，证据为operation-r2/independent-prelaunch.json。新journal费用字段实际为credential_mode=self_funded、allow_competition_credit=false，模型base_url保持ARC、glm-5.3-flash；根/advisor原生recipe随原恢复包保留。operation run仅调用一次，实际worker PID75733已accepted；尚未将该接收回执当作官网已启动，后续以新submission/run和原collector接受回执为准。

## 官网实际接续与采集器接收

唯一snapshot/create/start已完成，新submission `44201056bfbe`、run `7e8ec62670df`，journal pending=null；首次官网GET为QUEUED，platform_result.billing_mode=self_funded。原monitor目录hosted-sheet-r2已由单一新collector PID77062实际接收该journal/run/submission，first_batch为 `monitor/20261002T031836.502983Z`。原scheduler.done中的Sheet f16834f58674与旧GitHub e1aa595f6995保持，旧collector自然退出；不创建并行collector。独立进程身份与accepted读回保存于operation-r2/collector-accepted-readback.json。

当前只证明官网已接受启动及采集器接收；原生会话继续、新增内存字段实际样本及最终结果继续以同一collector后续保存的证据为准。

## 原生继续及新增OOM取证实际取得

原collector第二批 `20261002T032137.302066Z` 已完成，官网为RUNNING、部署completed、start_agent running、workspace_error/observation_error均无。原根native session `01a0f5f5-6f4c-716c-ba69-3270a25ea73d` 于2026-10-02 11:19:41 CST实际resume，原884000字节完整前缀保留，追加6990字节；新增assistant工具调用与toolResult见11:20:27、11:20:49、11:21:15，证明模型实际继续而非仅bootstrap成功。

新增8份memory_detail已取得PSS/Anon/File/Shmem、I/O与fd；native managed_state的expected/actual execution_id一致，并读回quiescent。采集前后内存实际取得。最新明细cgroup current为1943109632字节、limit2147483648，peak达到limit；file1288318976、anon522674176，max事件223、oom/oom_kill均0。这支持后续区分文件页/匿名页与限制触发，不足以认定OOM根因。capture.error原文 `evidence flush: 1 records, 6 ms` 已向主会话交接公共owner定向核实，不因此修改共享源码或重复启动。

派生有界事实及追加事件类型/timestamp汇总保存于operation-r2/runtime-first-evidence.json；原件保留在同一collector批次。唯一收费恢复和实际原生继续已完成，后续同一collector按既定3+8分钟节奏采集，终态及必要修复由主线闭环；没有其它收费尝试。


## ARC 额度耗尽后的供应商接续（2026-10-02）

用户最新明确：“7e8ec62670df使用的ARC API已经没有更多额度了，需要切换到我们自有API上，采用和I14一样的模型配方。”此项优先于I14新增生成。原官网owner获授权保全当前run、通过平台原生API发送唯一受控cancel并独立核对、取得取消后完整可得材料；不调用已退役旧writer，不伪造newexp停止证明。源错误/额度原因仍要以provider原件取证，平台RUNNING不代表模型可继续。

供应商按I14最新例外：Flash走普通Qwen，K3走自有Kimi，其余Token Plan。原I13 advisor为K2.7-Code，与I14 K3的型号差异独立记录，不因渠道切换暗改原生历史。主线与共享恢复worker核对模型wireID及保持旧provider/session身份的合法路径；必要的legacy source-stop导入门控和新daemon首次准入归DXowner完成有界设施修复。原包、原失败/partial、原collector均保留。恢复仅本GitHub/self_funded/比赛额度关闭，未开第二题/收费重试；具体新身份以实际回执为准。

## ARC额度耗尽后的自有供应商接续

用户最新明确要求run7e8ec62670df切换自有API，采用I14模型配方；主线授权本会话作为该run唯一停止/保全与恢复操作owner，共享源码只读，禁止恢复退役writer、伪造newattempt或新增采集器。私有范围为 `runs/iteration13/i13-2-20261001/hosted-github-self-funded-r4/`。角色型号是否将原K2.7-Code换K3待主线确认，之前保留原型号、无新模型请求。

原唯一collector最新完整批次061253Z实际保存72条glm-5.3-flash原生HTTP402错误，首条2026-10-02 14:04:08.870 CST：code=insufficient_balance，message=access key balance is exhausted，type=billing_error，具体request id及路径行号保存在quota-errors.json。取消前ZIP324460452字节已独立复制，SHA256 `93365b2468b76085e8ab01474ddf2a6235734a67cfe6efd525a8783a55764a44`，未当完整checkpoint。

当前API GET核对run/submission与旧journal pending=null后，先保存唯一cancel-intent，再通过平台原API POST cancel一次。HTTP200/curl0；随后独立GET于14:18:55确认CANCELLED/self_funded、身份一致。取消HTTP/body/stderr与停止观察保存在source-stop/，未调用退役writer或改原journal。取消后最终ZIP下载中，取消前副本及collector原件不覆盖。

新lab.exp stop-evidence要求新attempt的真实execution_instance/backend_identity；旧官网run无newattempt，不能手工伪装。现有producer在Mac运行会误记OS/root，需Linux同logical root实际离线生产；平台clone私有.git可能缺失，必须先核对最终ZIP，partial不能prepare。主线负责合法legacy停止证据消费边界、逐模型endpoint/key绑定及refresh/override组合，接口ready和型号决定到位前不发新模型请求。

取消后最终ZIP下载成功（HTTP200/curl0），326459735字节，SHA256 `de0f9bfe1af401b49756bf6abfd314fc75641b208f37afa1f70f4d41e826d43c`。50523成员、18份native记录与取消前逐字一致，无前缀不符；成员无增删。最终仍无clone私有.git；origin发布refs已变化，develop为5455099e6dfb56f697e8c5a058e19cf35b960602，新增PR7为66b94381562e7cdc5106cf7908a1d8f26ccbd512。来源DB/WAL、原生历史、origin及工作树行已保存source-facts；应用/未提交文件完整留在最终ZIP。handoff.json提供可消费停止/原件/额度错误/覆盖与明确缺项，等待主线合法合同和型号/路由交接，未发新模型/收费请求。

## 三路供应商与实际离线派发

用户确定本次advisor保留Kimi K2.7-Code，只切供应商；DeepSeek逻辑ID保持deepseek-v4-flash、TokenPlan wireID为deepseek-v4-flash-0731，Flash/root/vision逻辑glm-5.3-flash走普通Qwen wireID ZHIPU/GLM-5.3-Flash。官网表单只注入一个key，private deployment环境不会自动进runner；现生产端显式支持manifest绑定的.private/model-env.json，入口只加载公开绑定所引用变量。私有r4/model-environment.json为0600，仅FACTORY26_MODEL_BINDINGS与筛选的QWEN_API_KEY/KIMI_API_KEY/QWEN_TOKEN_PLAN_API_KEY，未复制其它凭据、未输出key。

逐七clone及空application证据表与当前origin对象/原生成功commit-push闭合。旧源真实恢复Git回执为未变化clone的当前基准，PR5更新1625158、PR6更新fa4cab5、PR7为66b9438；原PR4仍89c4a3d（tmp takeover最新e97不是原clone）。完整文件diff独立核对，tracked无missing。重建仅生成基于确认commit的新index，不声称原staging/reflog/merge历史恢复，原ZIP始终partial。

新public import-source-stop实际导入旧birth/独立terminal GET与cancel原件，明确legacy-source与launch_permission=false，不伪装newattempt。主线advisor确认同一Linuxrepairjob可在repair/readback后直接checkpoint/prepare，source_identity仍表示被停止的原生成执行；derived provenance独立记录实际repairattempt/执行和原ZIPsha/逐clone依据，新complete仅描述修复后材料，不假称当前repairjob已停止。启动保留prepared门控及再次GET原runCANCELLED。

最终共享main/support/checkpoint冻结核对通过，新包SHA256 `fcfb34c5b71ec4c019155dce22700dc3df40eab4d94c2d772982bfc0bf984fd8`，720307721字节。旧3385e候选包保留。新lab.exp offline-repair-final已实际派发，experiment=i13-flash-github-r4-offline-repair-final-20261002，attempt=attempt-a0014e842919603b296661e9，controller PID94886；development-2首用准入原件与network:none实物合同已消费。单job执行原main --prepare-only、非.git工作文件/nativeJSONL/DBWAL独立字节核对、派生checkpoint/prepare。此刻仅accepted/launch_pending，未宣称实际准备通过或模型调用，未发新官网收费请求。

实际离线反馈保留两项失败：final第一项因私有driver装配/workspace/agent违反原包/workspace/submission根约束，mainexit1/769保留文件mismatches=[]；修正私有路径后r2进入真实材料刷新，但shared override strictresolve request.pi.home时报FileNotFoundError，平台未保存空work/home/.pi/agent。实际nativehomes/template仍存在，第二项769保留文件mismatches=[]、无模型请求。两attempt/container已退出，终态archive preserved；第二错误已交sharedowner最小修复，本会话共享源码只读，不凭失败目录缺失丢弃原会话或改原件。


### 2026-10-02 自有供应商恢复：Linux 准备完成

主线转达用户要求尽快恢复官网，并将本次恢复的必要共享修复、Linux 准备、唯一 self_funded 提交与监控交接完整授权给本会话。原运行 `7e8ec62670df` 已独立 GET 确认 CANCELLED；其最终 ZIP 和所有原始失败回执保留。

新 Linux 实际执行 `offline-ready/attempts/attempt-34346ff16ed9172662501d43` 在 development-2 的冻结 amd64 runner 上关闭网络完成。实际入口退出码为 0，769 个保留工作文件、原生 JSONL 和 SQLite 文件逐字节一致。公开 checkpoint 和 prepared 均为 complete，prepared producer 已 published。原始官网 ZIP 仍为 partial；恢复的 Git index 是依据已有提交证据重建的新索引，不宣称恢复了原始 index/reflog。

准备产物入口为 `runs/iteration13/i13-2-20261001/hosted-github-self-funded-r4/prepared-ready`，官网执行 recipe 为同目录 `hosted-own.recipe.json`。冻结配方是 Flash 普通 Qwen、Kimi K2.7-Code 自有 Kimi、DeepSeek v4 Flash 0731 Token Plan。唯一官网提交正在通过新 lab.exp 启动，实际 run identity 以 execution.json 为准，不能将控制器 accepted 当作官网 RUNNING。


### 官网实际启动后的需求版本阻塞

唯一新提交 `c4655fdd6bfd`、运行 `925e6ef9eaf9` 于 2026-10-02 15:30 CST 实际启动，费用为 self_funded。入口在模型前拒绝：`ValueError: current requirements differ from retained workspace`。新运行已 FAILED，未获得模型接续，不能报告恢复成功或有效零分。

原冻结需求 SHA 为 `bdc17d23265a6b1948aec150e69d0b2accfa37db4c569305c97be7ff7f3b0b8f`（292270 字节），新平台下发 SHA 为 `9480921cb3b7ffdc5f32cb76011ecc1d5bf9bfbf2cba38e3a092355ac88a54f8`（172653 字节）。解析树不同，65 个需求 ID 不变但描述与场景大量改写。差异为 r4/requirements-diff.txt，摘要为 requirements-change-summary.json，原始失败日志及 ZIP 为 r4/live/monitor。本次真实来源前提变化已经向主线升级：建议保留原冻结需求生成接续，显式记录官网现行评测版本差异；在取得决定前不越过需求身份门控启动另一笔运行。原源会话、Git 和模型配方保留不变。

新 lab.exp hosted 的 is_latest 假设已按实际 history 原件修复：API 当前仅给 created_at，删除资格不等于最新身份。旧 frozen controller 的失败保留；沿同一已保存提交使用具有真实代码 provenance 的新 adapter continuation 完成 create/start，未重复 snapshot，pending 为空。临时只读 collector 已完成终态采集并退出，当前没有这次新运行的存活 collector。


### 新版需求迁移已获授权

主线转达用户原话：“保留进度，迁移新版需求继续（推荐）”。本次显式替换运行的允许需求包，保留旧输入原件、迁移前数据库和所有原生 JSONL 历史，并通过 Braid 正常评论及交付读回通知现有负责人。新需求 SHA 仍严格绑定平台输入，不移除或放宽 SHA 门控。结果身份是“I13 进度在新版需求下接续”，不直接比较旧版分数。

公开输入差异为 `public-requirements-migration.json`，54 个节点至少一个直接字段发生变化，需求 ID 集合仍为 65 个。新包为 `package-revised/agent.zip`，SHA `ba4590390e827977777b6c0974da149fc12f150e99a061471c51d262fa3abef7`；同真实 Linux 上的 `offline-revised` 准备正在执行，不调用模型。之前的 failed run 原件保留，替代启动授权已明确取得。


### 2026-10-02 16:18 CST 实际接续与供应商阻塞

新版需求替代运行 `c5a3674c42c4`、提交 `9cdbe3e15239` 已实际 RUNNING/self_funded，入口日志于 08:11:50Z 明确 resuming Braid。新实验是 `hosted-revised`，实际 attempt 为 `attempt-cfec0a4364a4a8d9fe32d9c4`。原 run 未重新激活，旧失败 925e 不计有效零分。

唯一 workspace collector PID45337、birth1790928748.405152/本机boot_id 已记录于 `live-revised/monitor/accepted.json`，旧collector均结束。第二批 `20261002T081625.435209Z` 的 ZIP 有50777成员/18原生JSONL，所有原历史前缀一致，原 session 实际新增消息；首批只是恢复中不完整导出，不能当作丢失历史。新增 root/PR7 Flash assistant 请求均返回 HTTP400 `The product is not activated`，错误 type invalid_request_error/code invalid_parameter_error。原件和逐会话增量见 `revised-first-native-delta.json`，因此只有“原生接续”，尚无成功供应商响应。

已交主线确认普通Qwen账户对 ZHIPU/GLM-5.3-Flash 的产品开通/可用凭据；catalog GET200不证明开通。当前未取消运行、不换模型、不回退ARC，继续同collector等待具体用户决定。供应商侧直接激活现有key可能无需再次上传。Braid日志还保留辅助OTLP503，不能用其替代具体模型HTTP400原因。


本次新版接续也已实际采到8项cgroup内存字段。08:20:59Z样本为 memory.current1714524160、memory.peak/max2147483648，anon671207424、file912760832；memory.events max1088但oom/oom_kill均0，pressure avg10/60/300均0。原件为 `revised-runtime-resource-readback.json`，来源是同唯一collector的真实ZIP，不把达到peak或max事件误写为OOM。当前阻塞仍是供应商产品未激活的HTTP400。


### 2026-10-02 立即取消并按确认矩阵热恢复

用户原话：“好，请立即取消，然后按照我们前面确认的模型矩阵（Tasks 应该有记录）去修改该运行的模型配方然后热修复上去。”授权停止、保全及该范围恢复。唯一 cancel POST 已取得确认，独立 GET 为 CANCELLED，finished_at 为 2026-10-02T09:54:20.117823Z。原件在 hosted-github-self-funded-r5/source-stop。未启动替代运行。

最新完整095113Z快照实际16个native home路由均符合I13合同；本次恢复已取得521条Flash、28条K2.7成功assistant消息，最近Flash成功09:36:57.995Z，随后09:36:58.411Z返回429 insufficient_quota。此前产品未开通的推断已被实际成功响应否定。普通Qwen Flash、TokenPlan DS0731、Kimi原厂K2.7已生效，重新上传同路由不会修复额度。Tasks最新矩阵仍保留I13 K2.7例外；GLM5.3/K3普通Qwen额度路由不自动授权替换根Flash。已向用户提出明确型号选择，停止现场保全继续，依赖选择的型号修改及上传保持待决。


用户进一步要求“不应该啊，普通qwen也有glm-5.3-flash可用才对，你本地排查看看？”。冻结Qwen key与当前models.env一致，精确Flash直接POST200/18tokens；实际保留models配置+CLI微请求成功。针对最后429分支537条消息，ModelRuntime实际发送539条消息、713294字节请求，model为ZHIPU/GLM-5.3-Flash、URL普通Qwen，Authorization匹配QWEN_API_KEY且不匹配TokenPlan；170603输入+3输出token返回200/OK。证据r5/local-flash-diagnosis及actual-cli-diagnosis/large-native-facts.json。小请求成功不是额度充足证明；现大请求亦可用，此前429供应商具体原因仍未知，不再声明永久额度耗尽，也不改根型号。

恢复保持原Flash/K2.7/DS型号，在显式完整矩阵中补齐备用GLM5.3与K3的普通Qwen路由，并将factory26默认路由改为普通Qwen，DS独立显式TokenPlan，防止未声明其它型号落到DS wire ID。源选最近完整09:51:13Z ZIP，原完整native/Git/DB同点；停止后ZIP仍由原唯一collector下载，不另建loop。取消前后3m07s无已观察成功模型活动，但保留该证据限制，不把源ZIP称完整Git检查点；派生Git index保留原件和逐clone证据，PR2 HEAD仍有推断限制。


取消后唯一collector已完成终态采集并自然结束，最终ZIP344317234字节，SHA80dc8b4df25ed743735d5a1691a4eee868188fd6ba06ff7d1c29317ac628cca9保留。对源恢复点1441份工作文件/原生记录/SQLite比对，无文件或原生历史变化、无新增；终态只缺失原braid.sqlite3-wal，因此仍选含DB/WAL的09:51同点快照，不用终态ZIP覆盖它。完整对比r5/source-stop/final-comparison.json。

新模型包已冻结，真实离线执行attempt-2dd27789fe74dc4d30b847bc已accepted，development-2容器e6411f2f9b4608e91defd08b4c91b97bf6573640d150369fee00d48ef7dc760e已network:none实际启动；controller目前launch_pending不当作prepare成功。一次程序编排等待prepared published后输运/build/start，不执行重复模型或收费请求。

新来源stop-evidence改用真正newlab attempt身份，由扩展后的import-source-stop消费原冻结experiment/attempt/execution/dispatch及独立平台GET，不伪装legacy。sourceidentity/stop完全绑定，launch_permission=false；新启动仍独立GET同birth的CANCELLED。仅backends.py/__main__.py必要公共改动，旧controller冻结源和原execution不改。


### 用户停止热恢复，转向 I14 baseline 两根模型新运行

用户明确：“我感到失望，我们每次热恢复都耗费十分多的时间，甚至超过模型运行的时间；基于此，我安排了实验基础设施DX改进，但还需要时间，而比赛不等人；所以请你直接使用I14-baseline运行GitHub题，有两个variant：glm-5.3-flash和glm-5.3（因为之前I13的glm-5.3 variant没有结果）”。这替代当前热恢复目标；不再重打r5或启动官网替代。唯一source c5已取消，原collector自然结束；准备后的上传编排PID12674已SIGTERM、当前无进程，没有hosted实验目录/新官网run。原source、失败prepare与源码修复保留。

r5真实prepare入口exit1，原错误FileExistsError recovery-native-transport/originals；1441文件mismatches=[]、无模型请求。已在共享源码将每次transport备份改为独立时间目录，并保存prior receipt；语法编译通过，但用户转向后未重跑此恢复，不宣称修复实际闭环通过。新目标由tasks/iteration14/baseline-roots/packet.md持有，baseline从干净起点，两组均普通Qwen，旧baseline暂停现场不恢复。
