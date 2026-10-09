# I14 GitHub 实际启动闭环

本页仅保存历史执行事实。用户已授权清理不完整 I14，旧运行目录及系统盘 `~/.codex/factory26-i14-runs/20261002` 已删除；系统盘迁移违反用户最新的 WorkSSD 绝对规则，不是可沿用方案。当前状态和设计复核归 [夜间 packet](../overnight-plan/packet.md)。

2026-10-02。执行 owner 为本主线委派的 i14_launch。用户要求“I13 我会另外去推进。现在的重点是让 I14 运行起来”，随后明确“baseline 继续暂停，只运行另外三个”。范围为 cleaner/reviewer/e2e GitHub 原冻结需求；不迁移新版平台需求，不运行 Sheet，不操作 I13 或 baseline。

实际材料与原错保留于 `runs/iteration14/dx-launch-20261002/`。Development-2 沿真实 first-use authority，2 GiB/2 CPU、同 daemon 五槽，不接管 WSL 旧资源域。模型为普通 Qwen Flash 精确 wire ID `ZHIPU/GLM-5.3-Flash`、GLM-5.3、K3；内部 DS0731 为 Token Plan，不可成为 Braid 成员；昂贵模型合计仅一个 Braid session。凭据只读 `.secrets/models.env`，私有制品不输出值。

cleaner 采用原完整停止快照。reviewer 已按出生身份停止其原冻结生成容器，完整复制 template（含所有 Git、Braid DB/WAL 和 native），只关闭本源 accessor/helper 和旧 operation worker/controller/adapter/owner/monitor；保留 source volumes、原 error 与 unknown。两 worker 被 kill 后成为共享 paused dispatcher 的僵尸，实时 Z 证明其不能执行；dispatcher 与 baseline 保持。两来源通过新 legacy-Docker 导入和即时当前来源核查，未补造新 attempt。

e2e 首次实际断网 prepare 未调用模型，因两份 tools/__pycache__ 同时被 manifest 登记与 verifier 忽略而失败；已修复公共 packager metadata 过滤，保存旧 ZIP 和原 stderr。canonical e2e 接口按逐模型 route 冻结独立 E2E_MODEL/BASE_URL/API_KEY；它使用普通 Qwen Flash wire ID，不依赖根逻辑 ID。r3 实际 Linux 断网 prepare `attempt-7a891ac90b533206b3ddb10b` exit0。正式生成已派发至 `e2e-generate-experiment-final2`，实际模型成功仍待 provider/native 活动证明。

canonical 恢复入口增加显式 `--execute-prepared`，复用原环境和执行段，不二次解包/刷新；当前 routes 与 prepared transports 相同才允许使用当前 deployment 凭据执行。cleaner/reviewer 最终包正在此版本重新冻结，尚未声明生成启动成功。实时执行与监控身份随后写入本入口；唯一 monitor-index 与 monitor-binding 位于 `runs/iteration14/dx-resume-20261002/`，复用既有 heartbeat 和 Console。

原 e2e generation 因 `resource-latest.json` 缺失等待，并未启动 Pi 模型；已通过公开 stop 保留该 container/run。原因是 runner 外部 OTLP 接收器替代了 standalone collector，而后者原来同时产生资源样本。现有 runner 循环已承担同 Docker namespace 的基线、每两秒及最终样本，将 `FACTORY26_EXP_RESOURCE_SAMPLE` 传过 internal_entry，终态保全包含资源原件。Docker `memory_bytes` 只由 cgroup 执行，不再误用为每个 Pi 进程的虚拟地址上限；本地 Linux entry 保留原限制。

当前真正 e2e 生成入口为 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002/e2e-experiment`，attempt `attempt-482e5780ca417e6ebb63e28b`、cid `aecd15534ef849c80bb1d8d20e22fbea2e4dba1f155db921ce008c12bf4eee12`、Braid `20261002-105607-3c89d659`。`e2e-native-activity.json` 已读回十条成功 assistant/toolUse，普通 Qwen route、精确 Flash wire；样本 age 0.93s、memory.max 2147483648、Pi AS unlimited。`e2e-live-route.json` 同一原生 home 实际 models.json 展开验证普通 Qwen endpoint 和 wire；不含凭据值。

两旧 cleaner/reviewer 离线 checkpoint 的 partial 原错揭示了材料绝对别名及旧 PulseAudio 临时链接。canonical 恢复已改相对材料别名，仅移除明确的已停止 Pulse 临时链接并写 literal target/reason 回执，来源原 ZIP 不变。`--execute-prepared` 消费现有公共 runner assembly/prepared 身份，避免把原始 ZIP 的无派生目录校验错误用于已装配材料。新两包已核实 canonical main、resource env 和当前单昂贵 Braid session guard；重新 prepare 正在运行，尚不将 prepare running 称作模型成功。

WorkSSD 的 12 GiB 本机存储准入拒绝原件保留。`/Users/lanzhijiang/Development` 实际是 WorkSSD 链接，第二次拒绝揭示了路径错误；真正新实验 root 已实查为系统盘 `.codex/factory26-i14-runs/20261002`，不删除旧现场。stable `monitor-index.json`/`monitor-binding.json` 与 `launch-handoff.json` 均位于约定 `runs/iteration14/dx-resume-20261002`，索引使用新实际绝对路径。

旧 reviewer prepare cid `516628...` 的整份 `/attempt` 返回超过 300 秒，保留 partial export 与 transport-error；当前确认为 exited/Pid0，inspect 已在 0.4s 内恢复。该恢复旧输运不重启 entry，且不代表 generation 失败。新的 cleaner/reviewer 初始 copy 窗口已关闭，后续 exporter由各自原 controller 在终态触发；没有第二 collector 或额外轮询循环。当前 physical 精确过滤 `io.factory26.exp.attempt`，Redis 没有该标签，不占实验槽；本三项与另一 owner 的两项新 baseline 共用五 Factory 槽，以实际 admission 为准。

cleaner 新离线 prepare `attempt-0d89fcc2eef74292a4ef85e0` entry exit0、checkpoint complete/gaps[]，五 Git 仓库 fsck0 与原生历史完整读回。sealed prepared output `artifact-c4131e0cce48851c97ac06e8` 已独立输运，两端 exit0，耗时 660.924s；公共 artifact verify 成功，receipt 为系统盘 root 的 `cleaner-prepared-transport.json`。cleaner generate 已经 compile/build，公共 start 接受 controller `controller-4e37834689cf6ed99b5bc7de`；这只表示控制器受理，尚无供应商成功。

reviewer 精确 node-gyp Python 外链已在目标 image 合同内物化为实际解释器，原始快照不变。新 prepare `attempt-ef630a2f3aa6a6608a020bec` 保留同 attempt，先遇 Docker info10s超时，后公共重入遇17对象整批 inspect60s超时；后者位于 admission reserve 前，但本地 accepted receipt 已存在，当前 launch_pending。原始 `launch-error.json` 保留，未假释放容量或重复入口，正在闭合其严格公共恢复条件。

reviewer node-gyp 实际准备已 exit0，`reviewer-nodegyp-checkpoint-readback.json` 确认 complete/gaps[]、7 个 Git 仓库 objects/head 读回均 exit0、3 native profiles 保全。`reviewer-nodegyp-build-tools-readback.json` 的原件 SHA 与 checkpoint 同文件相同；仅 pr-3 的 exact python3 外链被物化，记录 literal `/usr/bin/python3`、actual `/usr/bin/python3.12`、SHA1319c137...与冻结 image_id。sealed prepared 为 `artifact-a90c3ff6e9185d061f8cae77`，manifest `fd8dc01bf63ac36b754cc82db6424a6b749f60de2a86419e67ca2a63e1356ced`。

reviewer 本机整域 export 的 T+A+原reserve下限为25,775,698,327 bytes，读取时free9,609,064,448，至少缺16,166,633,879。仅关闭其本机 controller485，born核对后SIGTERM/lost；`reviewer-nodegyp-storage-hold.json` 保存依据，远端 archive/entry 未停止。下一步独立 sealed output 输运与生成不把离线成功当模型成功。

cleaner generate attempt `attempt-521bc2eaaaf45445b2075f6c`、CID `a3e6ab0f5887541aa3a380283bb403b2e900b2dae8235f449b62052651aec821` 已创建但首次 input cp300s超时，原error与unknown保留。公共 `continue-input-upload` 按同未启动容器接续：完整archive流读回、再次来源停止门控后共用原start/bind/marker，不重建或重复模型。原管理工具版本留存 `management-source-input-upload-v1.json`，本轮共享大cp窗口已修至1800秒。实际生成成功仍待供应商原生活动。

用户随后要求“暂停继续推进cleaner和reviewer；专注e2e。”已中止 cleaner 的本机 confirm-start-binding 工具66617并核实lost，关闭其本机 controller17020，未补 resource-start marker。公共 pause 回执将已启动等待marker的同CID置为 paused，StartedAt12:12:54.911579424Z；entry/Braid尚未启动，prepared/原error/完整readback均保留。reviewer entry0、完整checkpoint与sealedprepared保留，原远端archive允许自然保全，已关闭本机controller、没有启动新输运或生成。`cleaner-reviewer-user-pause-local.json` 集中保存实际身份、原件与操作闭合；stable index现在只消费e2e，binding保留两暂停项身份并明确advance_authorized=false。三项未闭合的源码/输运修复保持当前现场，不继续推进这两项。

2026-10-02 全部实验暂停交接：最新人类指示为“暂停目前现有的所有实验，因为 API 额度即将耗尽”。本 owner 停止 e2e 热恢复、prepare、transfer、新 attempt/start、评价和源码修复推进，不解除 cleaner 暂停，不重启已退出来源。公开暂停回执为 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002/all-experiments-user-pause-20261002.json`，stable index/binding/handoff 已标注暂停；heartbeat 由其全局 owner 暂停，本 owner 未修改自动化。

原 e2e `attempt-482e5780ca417e6ebb63e28b` 的实际 binary 为 e002，旧 ZIP file manifest 与实际进程一致，但 sources.braid/runtime-source 声称 63fd，原冲突记录保留。额度暂停之前已完成公共 pause、同一时点全 template 保全和公共 stop；来源 CID aecd15534ef849c80bb1d8d20e22fbea2e4dba1f155db921ce008c12bf4eee12 现 exited/Pid0，FinishedAt 为 2026-10-02T12:42:18.263619694Z。`e2e-oom-source/template.tar.gz` 传输 exit0、412992296 bytes、74.004 秒；同点 ZIP 为 491412908 bytes、84819 entries、SHA 04a7dc4ac07ca736fc4656550c08e29c96d0f4405848b51940fa7fc5a498578c。完整 checkpoint 语义核验尚未执行，不称恢复已完成。

实际 linux-fix 63fd 二进制已与成功 build receipt、源码 tar 和 source identity 核对，独立新 base 及 adoption receipt 保留；未启动新恢复 attempt。新恢复 package 实际返回 exit1：`KeyError: "There is no item named 'template/requirements/requirements.yaml' in the archive"`，原错误在 `e2e-oom-package.stderr`。fresh e2e 的 driver 将需求放 template 外，完整 template 快照没有该条目；已有冻结 requirements 制品保留，可在未来获准接续时显式绑定，当前不补 ZIP、不重打包。定向已有日志 modelScope 检查未命中，证据 `e2e-modelscope-log-audit.json`，不据此宣称所有原生会话均无该错误。

N 与原 P 范围共 11 个 controller 均经精确 process birth 核对为 lost，包括 e2e PID30186；没有本 owner 在途本机 prepare/copy/package/评价。最新 cleaner CID a3e6ab0f5887541aa3a380283bb403b2e900b2dae8235f449b62052651aec821 保持 paused，StartedAt12:12:54.911579424Z，原 marker 未补；最新 reviewer CID d2d9811d1847ab9500c7de70a0d5161d514dfde92bbabad85cb37e9c0b050b46 已 exited/Pid0/exit0，原完整 prepared 和归档保留。暂停不将历史 execution.json 的 launch_pending 猜成活动模型运行。
