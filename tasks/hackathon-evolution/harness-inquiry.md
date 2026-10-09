# Hackathon Evolution Harness 接入调查

调查时间：2026-10-06（只读）。本报告只核对公开决赛规则、仓库入口和输出目录生命周期；没有读取隐藏评测器，也没有修改源码、运行模型或提交。

## 官方基线读回（2026-10-06）

主线已把官网下载物保存在 `runs/hackathon-evolution/inquiry-20261006/`：

- `initial-projects.zip` SHA256 为 `38c0457d9df5871d69604a53763b2514b9d6e1abde918364af2bc6a97fad8ba0`，包含 `github/` 与 `sheet/` 两个输出目录；
- `requirements.zip` SHA256 为 `7d4b7414c2ef00b4bace62ce3747581cf91077ca8ab0985dcb8602f69989b500`，包含两题公开 `requirements.yaml` 与参考图；
- 两个基线的 `.factory26/pi-minimal-vv/identity.json` 都声明 `variant=pi-minimal-vv`、主模型 `glm-5.3-flash`、advisor `factory26/kimi-k2.7-code`；这与当前候选 `variants/pi-minimal-vv` 相符。

ZIP 只读清单显示基线不是纯应用目录：GitHub 根还含 `.e2e-evidence/`、`.factory-e2e/`、`.factory26/`、`process-evidence/`、`template.yaml`，Sheet 含 `.factory-e2e/`、`.factory26/`、`process-evidence/`；两者均含既有 `frontend/`、`backend/` 与 `README.md`。`.factory26/pi-minimal-vv` 内已有旧 `session.jsonl`、`events.jsonl`、`result.json`、`pi-timing.jsonl`、`user-instructions.md`、`home/`、浏览器状态和后台任务证据。它们属于上一轮运行现场，不能当作本轮 Pi 会话或新的应用输入。

## 当前可用证据

决赛公开规则要求平台在启动智能体前把上一阶段基线应用注入 `--output-dir`，智能体只需在该目录增量修改；不能清空、重置或整体覆盖目录。GitHub stages 的回退和最佳运行选择由平台完成。队长登录页面取得的公开需求和基线下载物已由主线保存于 `runs/hackathon-evolution/inquiry-20261006/`，具体身份见上节；本报告不读取隐藏测试或 native rollout。

仓库入口索引明确把 `pi-minimal` 作为独立原生 Pi 参赛实现，把 `pi-braid-i14*` 作为 I14 Braid 变体；见 [variants/README.md](../../variants/README.md)。近期顺序 stages packet 已保存一份真实 Stage1 工作区读回：`tasks/pi-minimal/sequential-stage2-stage3-20261006/packet.md:27-31`，但它属于本地 Stage2/3 准备，不是决赛平台基线凭证。

## 各入口的输出目录生命周期

### pi-minimal-vv：固定 evidence/session 路径

`variants/pi-minimal-vv/main.py:35-45` 固定本轮证据根为 `output/.factory26/pi-minimal-vv`，并把包内 `ROOT/pi-home` 绑定到该根的 `home`。官网基线已经在相同路径放入上一轮 `home` 与旧证据；因此运行时不会得到空的新数据域。

随后 `main.py:54-64` 无条件写入 `home/.pi/agent/models.json`、所有内部角色、`settings.json` 与 subagent 配置；这会覆盖基线携带的原生配置。更严重的是 `main.py:101-108` 把 Pi 的 `--session` 固定指向已有的 `output/.factory26/pi-minimal-vv/session.jsonl`，而 `main.py:120` 以追加模式打开 `events.jsonl`，`main.py:113-114` 又覆盖 `identity.json`，`main.py:141` 覆盖 `result.json`。本调查未启动它们验证，以上结论直接来自代码和 ZIP 字节，但已经足以判断：若原样运行，决赛 Agent 会复用/污染初赛 native session 与证据，而不是开始一个隔离的新会话。

`main.py:83-98` 还把临时目录 alias 指向同一旧 evidence 的 `tmp/`，并将 e2e MCP daemon 的 `cwd` 设为整个 `output`；`main.py:147-156` 最后在 output 全树上执行 daemon 停止和 `cleanup_workspace(output)`。后者不会删除文件（见 `scripts/agent_support.py:667-678`），但会把基线内若仍存在的、cwd 落在 output 下的进程纳入清理范围。决赛基线当前清单虽有旧日志和状态，但没有把它们视为仍在运行的事实；这里只指出作用边界。

E2E 的固定路径也是兼容性观察项，但当前证据显示它与旧 `.factory-e2e` 不是同一个目录：`tools/e2e.config.ts:20-27` 把 E2E 输出设为相对当前工作目录的 `.e2e`，而 `main.py:94-96` 将 E2E MCP 的工作目录设为整个 output，所以实际写入候选是 `output/.e2e`。官网基线清单含 `.factory-e2e/`（旧 E2E report、trace、tests），源码没有读取该目录的消费者；它与本轮 E2E 输出或测试输入的关系尚未由入口定义。若同一 output 可能重跑，`.e2e` 也存在路径复用问题，后续方案需决定其状态边界。

其它证据消费者已逐项核对：`capability-evidence.ts:9-28` 只写 `PI_CAPABILITY_EVIDENCE_DIR`，`factory-pi-timing.ts:6-24` 只追加 `FACTORY26_PI_TIMING_FILE`；两者当前都由 `main.py:74-75` 指向固定 evidence 根。`main.py:92-99` 先从包内 `mcporter.json` 复制配置，再写入 evidence 下的 `mcporter.json` 并更新环境变量，未发现读取基线 `.factory-e2e` 的路径。`tools/e2e-cli:5-14` 只消费 runtime/addon 和浏览器库，不自行选择 output 目录。故需要修改的固定路径集合是：session、Pi HOME/native 配置、capability、timing、events/result/identity、TMPDIR/MCPORTER daemon，以及 E2E `.e2e` 输出；旧 `.factory-e2e` 仅是保留基线内容。

上述事实记录了该入口与含历史 evidence 的 output 组合时的路径关系；是否采用新的 evidence/session/home/tmp 命名或其它隔离方式，属于后续方案选择。应用本身由 Pi 在 output 根读写；旧 `.factory26` 是否由平台过滤、保留或另行处理，当前没有从入口代码得出结论。

### pi-minimal：直接在 output 工作

`variants/pi-minimal/main.py:21-43` 只校验需求目录、创建 `output/.factory26/pi-minimal` 证据目录和 `pi-home` 绑定；没有 `rmtree(output)`、`copytree` 到输出根或 Git reset。`main.py:86-109` 把需求写入指令，并以 `cwd=output` 启动 Pi；Pi 会在已有输出目录内读写应用。`main.py:135` 的 `cleanup_workspace(output)` 只扫描并终止工作区进程，`scripts/agent_support.py:667-678` 没有删除文件。因此平台注入的 `frontend/`、`backend/` 等基线文件会自然保留，模型可以增量修改。

当前指令要求在 `@OUTPUT@` 内实现需求，但没有专门描述 Evolution 的基线语义；这只是行为提示观察，不等同于运行时覆盖。

### I14 Braid：普通生成入口仍从空应用开始

`variants/pi-braid-i14/run.py:153-165` 创建新的 `output/.factory26/<run>/work/application`，但没有从 `output` 复制基线；`run.py:187` 只把公开 requirements 复制到运行证据目录。随后 `run.py:318` 调用 `initialize_repository(app)`，`scripts/braid_runtime.py:11-18` 在这个空目录初始化 Git，并提交空初始快照。故普通 I14 入口会丢失平台注入的基线，无法直接用于 Evolution。

`pi-braid-i14-cleaner/run.py:194-205`、`pi-braid-i14-e2e/run.py:188-201` 和普通 `pi-braid-i14-reviewer/run.py:250-266` 也分别创建空 `work/application`；Reviewer 只有显式 `--application-seed` 时才调用 `copy_application(seed['application'], app)`。这类 seed 是本地发布的 application manifest，不等同于平台自动注入的 output 目录。

组合变体 `pi-braid-i14-reviewer-cleaner-e2e/run.py:201-212` 已增加从 output 复制非保留成员的逻辑，排除 `.arc`、`.factory26`、`.git`、`requirements`、依赖和构建缓存；随后 `run.py:456` 初始化 Git 前会保留基线。该接线证明复制时机正确，但其交付仍调用 `deliver(run/'application', output)`（`:504`），而 `scripts/agent_support.py:712-726` 明确只允许输出目录不存在同名文件；Evolution output 已有基线文件时，最终交付会因同名拒绝覆盖而失败。这形成两个独立事实：它会消费 output 中的应用成员，但现有交付函数拒绝 output 中已有同名成员。

## Git/Braid 与需求接入结论

当前 Braid 约束是：应用工作树需要先有初始快照，Braid 从该快照继续；`initialize_repository()` 本身不会消费外部 output。若某个 Braid 入口接入 Evolution，需要定义平台注入应用成员与 `work/application` 初始快照的关系，以及 `.git`/`.factory26` 等平台保留路径是否留在 output 根而不进入应用快照。组合变体已有一套复制规则，可作为对照事实。

需求仍应按现有入口复制到 `run/input` 或证据目录供 Agent 阅读；不能把平台注入的 output 当 requirements，也不能把 `requirements/` 目录复制进最终应用。当前 I14 代码已分别通过 `shutil.copytree(requirements, inputs)` 保存公开需求，路径见 base `run.py:187` 和组合版 `run.py:237`。

## 兼容性待解决事项（不构成候选排序）

以下是各入口与 Evolution 输出目录合同之间的观察项，供后续选择任一候选时核对：

1. `pi-minimal-vv` 的固定 evidence/session/home/tmp、Pi native 配置、事件/结果文件，以及 E2E `.e2e` 输出，和基线内已有历史材料存在潜在路径碰撞；需定义本轮运行的状态边界和旧材料处理方式。
2. `pi-minimal` 同样在固定 `.factory26/pi-minimal` 下保存证据，但当前基线身份来自 `pi-minimal-vv`；两者的 evidence schema、session 位置和平台保留目录关系尚未做兼容性验证。
3. 普通 I14 Braid 入口从空应用初始化 Git；组合变体会复制 output 应用成员，但 `deliver()` 拒绝同名输出。若未来采用任一 Braid 入口，需另行定义基线导入和交付回写合同，覆盖新增、更新、删除、重命名、平台目录保留以及失败原子性。
4. `--application-seed` 是本地发布 application manifest 输入，与平台自动注入的 output 不是同一接口；是否增加适配层需依据实际候选和平台合同决定。
5. 需求已分别复制到 I14 的 `run/input`；`pi-minimal-vv`/`pi-minimal` 则将需求路径写入指令。两种入口的需求可见性已观察到，尚未进行决赛运行验证。

## 未知与下一步

公开需求和基线已取得并在 WorkSSD 保存；仍未知的是最终提交采用哪个候选 Harness、平台对 `.factory26`/`.factory-e2e` 等目录的最终上传过滤细节，以及各候选在决赛平台实际启动时的状态边界。上述未知会影响后续适配设计；本报告不据此选择 variant，也不读取隐藏测试。
