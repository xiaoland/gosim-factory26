# I13-2 官网 Flash/GitHub 失败后恢复

用户明确授权“flash/github 也请恢复”。来源为官网 run `377afa346c92`、submission `66774c63c885` 的 FAILED 终态，采用现有最新保全 ZIP，不回退较早阶段；原件为 `runs/iteration13/hosted-recovery-20261001/monitor/20261001T101157.239125Z/377afa346c92/workspace.zip`，SHA `88f2c0c85ffde65ea7fa5db8adb1b96c8692bd2188383f6e85d584177abb486b`。collection 与 status 的身份/终态匹配，原失败背景保留于 `tasks/iteration13/hosted-github-recovery-failure.md`。该终态是生成中断，尚未形成有效应用评分。恢复准备子任务只构建输入和无网络 prepare-only；主线随后完成唯一官网提交，准确新身份及首批证据见文末。

派生工作区保留 Braid run `20261001-052115-e45f4278`。原 request 的 root 为 `pi-glm-fast/glm-5.3-flash`；历史 `pi-deepseek-fast` 也已是 GLM、root-only 且不是 root，不加入 DeepSeek 可分派成员。原 Flash/K2.7-Code/ARC 模型材料、transport 与 native 历史作为原件保留。

平台 ZIP 遗漏所有 clone 私有 `.git`。root 的八个 tracked 文件完整匹配发布 origin 中可达的祖先 `828d17e76c962135b1d0827dc62c24ebf76d419e`；root 原生 session 第 71/72 行确认成功创建 base-scaffolding，第 85/86 行确认提交并 push 到 828d17e。此后另一 root session 的操作主要对临时 `/tmp` checkout 核验 PR；本次没有用 DB 的早期 main 登记覆盖这项实际证据。root 只重建 Git 管理信息，HEAD/index 为 base-scaffolding@828d17e，remote 为同一 run 的 canonical origin，不 checkout 工作文件。重建不能恢复原 staging、reflog、未发布历史或 merge index/状态；其它 clones 按既有恢复入口与各自发布 ref 重建。

PR2、PR3 为 MERGED，PR4、PR5、PR6 为 OPEN，develop 发布 ref 为 `4e4860cb59e8a0db86638af6603cbde59adff224`。相对各自发布 ref，PR4 有八个 tracked 修改及二十个额外文件，PR5 有十三个修改及三十三个额外文件，PR6 有两个修改及四个额外文件；这些文件与所有原工作树字节均保留。root 的 notes/task-packet.md、tasks/issue-1/packet.md 保留。原 reset `01a0f6e2-f0ab-79f0-9f8f-4713e17d69f2` 仍为 blocked、continuation 1、new_session_id null，具体 error 也保留，不能当作已完成 reset。

现有 Braid CLI 只向派生 Issue1 追加维护 comment37，并实际读回。输入要求先核对当前 Git/Braid/native 与未完成工作，读取独立新版 svc-documentation、svc-task-packet、braid-collaboration，依据实际缺项补齐并发布共享 packet/AGENTS 入口，保留现有 packet 和在途文件，再继续原需求。没有内联技能正文或导入隐藏评测。六张身份/工作树/reset 表的原有列及全部行 hash 保持。

派生 ZIP SHA 为 `95476f6e56cc15e12a5ca0b7aa4aa44b8c62819ec75154d49fbbd1c6873cb7d6`，307,342,748 bytes、28,274 个文件。原 28,244 个文件全部保留，仅 SQLite DB/WAL/SHM 因维护输入改变；新增文件只有 root Git 管理信息。35 个原 native session/model 文件逐项保留字节、行数与 SHA。证据均在 `runs/iteration13/i13-2-20261001/hosted-github-recovery/`：parent-index、root-ancestor-tree-matches、root-native-git-witnesses、root-git-reconstruction、all-worktree-preservation、native-preservation、maintenance-input/readback 与 receipt。派生时 ref 拼接错误使新建 HEAD 暂未绑定，修正了本次新 `.git` 后接续；原失败命令/错误单独留存，没有改原 ZIP 或工作文件，未重复追加维护输入。

最终包已复用既有 `i13-2-flash-base-r2.zip` 与 Braid binary `9d322da9…`、编译 source `89d19889…`。本项新建的独占 prepare 容器为 `04b15bb1a2f315fb93ca5fb5797d758bab30d3fbbcc52887b9a36487d8a37985`、`factory26-i13-2-hosted-github-prepare`，network none、Mounts=[]、4GiB/2CPU、uid/gid501:20；不操作现有生成、Console、monitor 或上一项已停止操作容器。最终真实 prepare-only 与停止保留回执如下。

最终包 `flash-root-github-resume-r2.zip` 已冻结，SHA `bd897c86b9dbb56186d3929522e01d2dff19d76fb940f1b613e00ee80751f615`，701,169,017 bytes，manifest SHA `03bcbd36d40e09a2387e01e198a237ad2cc4267f41dd2c44eb58d5fb5239256b`。它使用同一 Flash r2 base（SHA `32133dad…`）、Braid binary `9d322da9…` 与明确编译 source `89d19889…`；main.py SHA `ffae3f08…` 与通过的 Sheet r2 恢复入口相同。完整 package receipt 与索引在 `flash-root-github-resume-r2-evidence/`。没有重建 base 或修改 canonical 源码。

实际 Linux 操作使用 `/workspace/submission/agent/main.py /workspace/requirements --output-dir /workspace/template --prepare-only`，uid/gid 501:20。七项传输均确认 exit0 后只调用 main 一次；验证包/工作区时耗时较长，一次现场读取确认 main 为 D 状态、stderr 空且尚未 restore，没有把该等待归为模型 stale 或新增 OOM，也未重发复制或创建。随后 main 和包含保留核对的操作脚本均返回 0，stdout 明确记录 prepared without starting Braid，stderr 为空。实际命令、prepare 分支 return 原文、无网络无挂载的独立容器前提和原始输出共同支撑无模型准备边界。

实际 readback 的 `receipt.json` 保留真实字段：786 个当前应用/私有 origin/实际 SQLite 映射工作树/native 文件无差异，35 个 original native 文件的字节、行数、SHA 保持；六张表全部原 identity 行、worktree map 和 work item 状态保持。root 的实际 HEAD/branch/remote/status 与派生重建完全一致，未提交的共享 packet 继续保留。PR4、PR5、PR6 的在途文件均包含在逐字核对中，原 blocked reset 及 error 保持。完整 profile 配方、root 与 legacy GLM 状态未改变；68 个技能文件与冻结包一致，56 个 retained-home 材料文件与刷新模板一致。runtime/helper 的比对依据是已完成 Sheet r2 实际 Linux 操作保存的 hashes 与本次明确冻结的 Braid9d322；本项新容器没有另造一份旧 `/runtime`。`runtime_matches_authorized_artifacts`、`helper_matches_operated_artifact` 均 true，comparison_basis 如实保存在回执。

实际原件及有界摘要在 `recovery-prepare/hosted-github-r2/`，包括 receipt、stdout/stderr、preserved-files、source-native-current、source-identity-current、worktree-map、git-current、root-git-current、context-resets-current、skills-current、native-materials-current、runtime-current 与 observations。据此可交主线执行唯一官网提交，原 Git staging/reflog/merge 状态缺口仍明确保留，不构成假恢复证明。该恢复准备子任务没有发模型请求、官网写请求或启动长期采集。

完成后再次核对完整新容器 ID、名称、network none、Mounts=[] 与本项 ownership label，按授权仅对此容器执行 `docker stop --time 10`。stop 返回 0，独立 inspect 读回 exited、OOMKilled false；容器和全部文件系统保留，没有删除 volume、原件或其它容器。停止前后 identity 与原始回执保存在 container-before-stop、container-stop、container-after-stop.json。主线已独立复核准备结果并接手唯一官网提交；本子任务不等待或监控新生成。

## 官网启动与监控交接

主线重新计算原/派生ZIP SHA，并独立比对15份原生对话JSONL；与来源一致。23:50:55 CST唯一snapshot/create/start流程完成，新submission为 `8fad2a412927`，run为 [e1aa595f6995](https://arc-bench.com/runs/e1aa595f6995)。冻结journal为 `runs/iteration13/i13-2-20261001/hosted-github-r2`，独立读回billing_mode与submission credential_mode均为self_funded，输入allow_competition_credit=false，pending=null。没有重新发送任一写请求。原恢复范围与私有Git缺口保持上述解释。

同一官网纯脚本collector已追加该journal，进程身份核验后48187→245，保留Sheet原scheduler与去重历史；未启动第二条官网collector或审查模型。接线回执为 `script-monitor/github-attach-receipt.json`，现行PID/命令归 `hosted-sheet-r2/monitor-launch.json`。23:51:07 CST首批采集 `hosted-sheet-r2/monitor/20261001T155107.297047Z/` 读回RUNNING、deploy_agent=running、start_agent=pending；classification=preparing、errors=[]。该证据说明平台部署已开始，尚不证明新Pi恢复或应用进展。后续3+8采集、provider状态判断和终态保全由现有脚本持续完成。
