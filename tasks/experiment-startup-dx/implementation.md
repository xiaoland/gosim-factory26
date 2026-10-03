# 实施与反馈

源码在 feat/experiment-startup-dx 隔离分支实现，未修改主工作区或接管实验。`local_job` 是公共 ARC job 构造与输入角色解释边界，arc_matrix 与 intent compiler 共用；低层 recipe 仍为 local + external_docker。

高层 generate 使用 `operation: arc-local-generate`、`purpose: generate`、agent/requirements inputs 和 limits；case.backend 只选择 competition_id/task，环境 `arc` 使用 sdk_source 与 target（完整 endpoint、immutable image_id、slots、admission_volume、authority_handoff，可选 python）。command/backend 由设施生成，拒绝模板手工重复权威。Python 用 `{runtime_python}` 由实际 runner deployment 解析，不与 runner SDK input 同名。native 模型 bindings 由 models 冻结。

build 在实际绑定后读取宿主 SDK main/run_container 与来源SHA、Linux/amd64 Node/Braid ELF头及公开需求；目录材料消费真实已发布artifact的producer provenance，ZIP才读取package-manifest。不向不可变目录补manifest。未生产 from_production 在compile保持关系，在doctor显示等待；不为compile安装runtime或提前生产材料。admission与doctor共用协议2卷身份解释，保留真实旧卷拒绝和handoff边界。

adapter在单一环境文件生产处合并编译公开模型政策、选定凭据变量，冲突只报告key；SDK子容器创建后、启动前按真实Config.Env读回，回执只保留变量名、公开政策hash及container identity。新contract的wrapper从设施冻结ResourceEvidence实现在实际子namespace取得cgroup并持续采样，发布本namespace services；bootstrap及已启动collector归同一try/finally。旧无contract入口保留process.wait，不强制其提供新的Factory support。未执行子容器，以上是已实现合同而非已观察运行结果。

实际反馈入口：

- actual-material-readback.json：现存I14 Linux ZIP、实际宿主SDK与公开GitHub需求的离线角色读回。
- actual-directory-readback.json：真实material-591f24ea目录和producer原receipt读回，该目录无package-manifest，未补写或修改原材料。
- actual-plan-readback.json：由实际I14输入/模型/目标身份派生的完整compile成功，from_production保留；宿主runtime与材料均build-required，未创建producer cache。首次失败的endpoint可选environment字段假设已修，原错保留在runs/experiment-startup-dx/offline-plan/compiled。
- example-intent.json 与 example-environment.json：本次真实公开计划的可复用输入示例；authorization明确仅离线用途，不构成模型/Docker启动许可。
- source-readback.json：10个当前源码及两个生成wrapper的内存compile身份。有限git diff --check通过。

没有运行SDK、Docker、模型、平台、测试/模拟/探针/smoke，没有生产或复制大材料。没有测量实际启动耗时，没有取得子容器真实环境、ResourceEvidence或模型首次活动验收；这些需要另行已授权运行。主区并行修复重叠仅精确采用adapter的read_json与runner的platform import；不复制agent_support的variant内部单次bootstrap或其它在途改动。


## 已授权架构改动

2026-10-03 用户指示“开始改动”，本节记录四项共同合同的实施。前文 ARC 局部改动的读回保持原身份，不作为本节完整生命周期验收。

定义生产按 variant、runtime、skills、support 分组件冻结，再组合为 definition；SDK 目录与 Hosted ZIP 是缓存交付投影。Fresh、prepared 与 child 将 reference/member、实际 namespace、可写 state 及服务装配为共同 execution context。四 I14 消费该上下文，恢复入口继续保留其原生接续语义。控制器源码属于执行器闭包，修改它不使 Harness runtime 或交付定义失效。

Workspace 每次获取单次封口供输出与终态 archive 消费，archive 保存关系而非再复制运行树。完整 managed 快照可继续供 checkpoint 复用，普通终态快照不能补 closure 追认。Docker 默认在 daemon 内通过只读状态 capture helper 封口；显式 export 接收已经封口的资产与定义关系，回执不声称已安装可变 workspace。受管 `.scratch` 仅用于同盘生产移交，失败保留，不能自动当垃圾删除。含省略定义目录的快照有明确排除关系，普通消费者不能把它当完整目录。

同次发布的实际内容读回只通过内存 PublicationWindow 复用；持久记录不含免检许可。新的消费窗口仍核验实际字节。受管 state 负责 capture、repair、generation 和唯一 writer 交接；半修复不使用旧 snapshot 的内容证明。独立 advisor 已发现并要求修复普通 whole-output 兼容、Docker member 实际安装和启动前写者登记的竞争窗口。

定义、交付、装配、执行上下文、state 交接及所有已识别 caller 已实现。SDK 父侧认证 daemon 组件并只读装配实际成员；工具凭据是每次 attempt 的私有输入，不改变共享定义所有权。新目录与 ZIP 提供标准根入口及依赖，清单按最终写入字节生成；原包 run.py 不匹配的实际读回见 experiment29-package-readback.json。失败预约按明确生命周期取消或删除从未启动的具体容器，再释放容量；辅助对象只按本次创建责任处理。创建结果未知时保留现场。

SDK 终态走公共 capture 并发布整个实际 stage，随后从不可变快照接收官方 inventory；不另建旧 capture 租约，也不声称 SDK resume。公共 checkpoint 根据唯一或明确选择的已登记 child，从实际 stage/state member 生产 schema4 小元数据，保留 child 出生身份及 outer 关系；非零入口不自动抹掉已验证来源。Local 原生工具尚无完整脱离父进程后的登记/关闭合同，所以新完整 capture 明确阻塞。普通 Local 终态内容封口与完整恢复 capture 分开；已知执行和写者终止后，named outputs 可以从隔离的不可变内容发布，明确 terminal-content-copy 与未证明的跨文件切点/未知派生写者覆盖，不绑定 holder 恢复快照。内容封口失败时 archive 只发布 terminal-evidence-only，原状态保留。后来取得 closure 必须生产独立恢复快照，不能升级旧普通制品。

实际操作读回见 architecture-operation-readback.json：已发布的实际 executor 支持源码完成 source→publish→retain/resolve→member 安装，并从该 payload 独立解释器导入所需模块。该材料很小，原件中的耗时不能推广为完整打包、启动或恢复提速。该操作保留其当时源码身份，后续修改不倒填为已执行。现存 A2 的保存事实已由 projection 解读及渲染，见 architecture-provider-readback.json 和 architecture-provider-render.txt；没有新采集或平台请求。

最终 40 份改动 Python 源码与 11 段静态嵌入 Python 的内存编译身份见 architecture-source-readback.json，git diff --check 通过。独立 advisor 对 SDK capture、失败清理责任、最终交付及 Local 捕获边界完成定点复核；源码阅读不替代实际运行。没有启动新 Docker、SDK、模型或远端实验，也没有编写或运行设施测试。未找到可用于完整恢复操作的真实新分层 Harness 检查点，因此完整恢复反馈和三类耗时仍待实际运行验收。


本轮生产与装配接缝已替换为共同入口。四个 I14 的 `build.py` 只声明技能选择并调用公共 producer；agent、runtime、skills、support 和 E2E addon 分别发布，component cache 的受管 payload 在发布时移交，后续保留原引用。工具默认凭据是既有两键的独立私有输入，未进入共享 agent；只影响相应交付派生输入。Delivery 保留原资产字节，按独立目录映射 role，外层标准入口及 requirements 是投影，最终 ZIP 对实际写入字节生成清单。ZIP 与目录在 SDK 消费端均识别 delivery-layout，而不是新 ZIP 再走历史 wrapper。

Local 保持 holder 私有稳定 role 路径；变化定义只能在受管 capture repair 中替换记录过的 alias。入口及受管原生 launcher 在创建进程前登记 launch-pending，子进程绑定真实 birth 后核验许可再 exec。Docker payload 消费外层权威已接受的 permit 和已有 retention，不要求工作负载访问控制宿主 Docker CLI 或写只读 store。SDK bridge 在 child create 前安装共享 daemon 缺少的 component references，由父 helper 认证 member 和持有依赖，然后将实际 payload member 只读绑定到本 namespace 的 role 路径。Child common bootstrap 消费本次真实物理 birth 对应的 placement，不传播宿主 root。

实验29原件确认 `run.py` 实际 SHA 为 `99e9e6ca9d00fa664985f567f1c9341cc09000e8ebbe887fe81dea027570e0ab`，旧包清单为 `83dd476304d5536a17ed768c27db7c1fd305cfa25f9bfdc1386455743554f1d8`，入口抛出 `ValueError: 参赛载荷哈希不匹配：run.py`。见 experiment29-package-readback.json；这证明执行程序已进入 Harness，仍没有模型调用证据。新 producer 拒绝历史 root delivery manifest 作为 definition source，先冻结最终源码及公共 bootstrap，再生成 delivery 清单；instrumentation 不修改新 delivery 文件。

实际小材料操作见 architecture-operation-readback.json：当前真实 executor 源码闭包发布到 WorkSSD artifact store，读取保留的 scripts member，安装稳定 support alias，并由独立解释器从已发布 payload 导入六个实际模块。该回执只证明这次源码资产生产/装配机制；它不是完整 runtime、Harness prepare、SDK、服务或模型运行。architecture-source-readback.json 保存对应时点的源码内存编译身份；最终集成后应更新到最终代码。原件不冒充本轮打包、首次模型或热恢复耗时测量。

最终源码采用关闭了两个必要回归：SDK domain prepare 使用实际 metadata 字节读回，不引用不存在的自 hash 字段；位置绑定只更新 domain/store 字段，不覆盖 definition reference。普通内容与恢复获取的 provenance 分别保存，完整 producer 核对快照发布时的 request/token/closure；取得新 closure 不提升旧普通副本。同代原 managed snapshot 保持可复用，避免不必要的重新封口。
