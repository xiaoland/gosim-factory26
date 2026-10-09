# Pi 机械公共基线收敛调查

当前决定是仅持续维护 pi-minimal-vv，旧 pi-minimal 源码、guard 与运行证据保留。本轮没有更新活官网 d37、生成模型、构建提交或提交 Git。角色目录发现修复已由现有当前源码采用，本轮补齐两原生 builder 的装配 guard；d37 实际源为 pi-minimal-vv-text.zip（b7f2ba5959951c158a49e6e76a69ca4444a6305e78c3dfc1b5b19e82d91f62b3），main 无 catalog 开关、runtime 无 hook。

## 实际生产边界

`materials/npm/package-lock.json` 锁 npm 依赖；`materials/npm/patches` 持有补丁。`tooling/scripts/runtime.py::native_patch_specs` 已给出完整有序列表，`prepare` 按顺序应用并写补丁及最终目标文件 SHA stamp，后来补丁覆盖先前目标时，stamp 在最后统一生成。Linux producer 的 runtime-source 保存锁、补丁和 native-managed 模块 SHA。`derive_linux` 拒绝旧锁/补丁身份，另核 Pi retry 实际字节；因此已存在可复用的公共 producer，而不是从零建立。

Dockerfile仍手写同顺序14次patch；runtime.py创建临时Docker context时把当前materials/npm材料映射为harness/npm，因此 Dockerfile COPY 的旧路径是构建上下文命名，不等于继续消费仓库旧目录。两处顺序仍需由一个已有清单驱动，防新修复仅加一处。

| 补丁（实际顺序） | 职责 | 目标文件数 |
| --- | --- | --- |
| `pi-background-bash-1.0.5.patch` | 公共原生能力/失败边界 | 2 |
| `pi-subagents-0.56.0-completion-boundary.patch` | 公共原生能力/失败边界 | 4 |
| `pi-subagents-0.56.0-model-exclusion-boundary.patch` | 公共原生能力/失败边界 | 3 |
| `pi-subagents-0.56.0-open-tools.patch` | 公共原生能力/失败边界 | 2 |
| `pi-subagents-0.56.0-acceptance-off.patch` | 公共原生能力/失败边界 | 22 |
| `pi-coding-agent-0.85.1-braid-boundary.patch` | 混合通用机制与 gated Braid 分支 | 8 |
| `pi-ai-0.85.1-connection-reset.patch` | 公共原生能力/失败边界 | 1 |
| `pi-coding-agent-0.85.1-compaction-threshold.patch` | 公共原生能力/失败边界 | 4 |
| `context7-pi-0.1.2.patch` | 公共原生能力/失败边界 | 3 |
| `pi-fff-0.11.0.patch` | 公共原生能力/失败边界 | 1 |
| `pi-coding-agent-0.85.1-i13-2-managed.patch` | 生命周期适配（按执行环境启用） | 2 |
| `pi-background-bash-1.0.5-i13-2-managed.patch` | 生命周期适配（按执行环境启用） | 1 |
| `pi-subagents-0.56.0-i13-2-managed.patch` | 生命周期适配（按执行环境启用） | 5 |
| `pi-subagents-0.56.0-catalog-hook.patch` | 公共原生能力/失败边界 | 1 |

Pi核心的 braid-boundary 名称不能当作全部Braid专属：willRetry传播、terminal error退出及edit/grep/find说明是通用；取消标记、项目root资源发现等分支明确以BRAID_AGENT_RUNTIME启用。compaction patch添加thresholdTokens能力和校验，阈值取值仍由执行配置选择。connection-reset修Pi SDK网络retry，不等于模型供应商路由。PBB公共patch包含后台/服务语义、有限任务completion、批次通知、error/aborted与willRetry边界。subagents completion修会话ownership、结果drain与截断识别；open-tools保实际能力开放；catalog仅发现元数据；acceptance-off移除该插件自动acceptance gate，不替代用户验收。model-exclusion-boundary改候选选择失败诊断，不持有各variant模型配方。context7/pi-fff修工具的提示/行为边界，同样属于共享工具能力。

3个 managed 补丁和 `native-managed.mjs` 是实际进程所有权/资源准入协议：启动确认、执行identity、进程树清理及managed provider状态。它们当前与公共补丁一起安装，但仅在FACTORY_NATIVE_RUNTIME_MODULE存在时启用，Pi Braid分支另看BRAID_AGENT_RUNTIME。统一安装不应把standalone的agent_end/drain完成责任变为Braid RPC完成合同。Braid实际provider和公共agent_support.runtime_resource_environment持有该环境与launcher协议，不能凭材料存在认定启用。

## 实际消费者及差异

| 消费者 | 当前实际来源/改写 | 收敛范围 |
| --- | --- | --- |
| pi-minimal-vv | 整runtime复制，E2E addon独立装配；catalog exactguard；builder还写PBB旧非TUI error-exit fallback | 当前活动原生消费者；改为完整baseline身份/目标字节guard，删除builder对runtime代码二次修改 |
| I15 reviewer-cleaner-e2e | builder核protocol所有patch SHA和retry字节，从native_patch_specs覆盖全部目标，再覆盖managed模块和实际Braid binary | 继续用公共Pi机械baseline；保Braid binary/build receipt和own resource/helper合同，不互相importvv |
| I14 reviewer-cleaner-e2e | 冻结base和自身binary/material overlay，未像I15完整采用当前公共target列表 | 保旧历史身份；若后续明确新构建维护再迁移，不改过去run |
| I14-dx-test | 独立Braid运行装配入口 | 仅按后续实际维护授权接共同producer；本轮不扩工具/角色 |
| pi-minimal | 已有catalogguard，但本轮停止扩展维护推荐 | 保源码/历史guard，不再跟进新功能 |

vv与I15都有subagents/PBB原生extension，但根/子角色目录、禁用builtins、工具能力ceiling、fresh上下文和实际继承配置不同；这些是角色合同，不能统一成某variant默认。vv还具有执行器拥有连接的E2E入口，属于工具能力的共享材料加原生接线，不能以Pi baseline让无E2E消费者自动具备该能力。观察/timing/能力证据扩展用于采集，不作为Pi机制真相来源。

`variants/pi-minimal-vv/native-async-startup.patch` 与公共managed subagent patch所含修复重叠，当前main/build没有消费该独立文件；它是历史材料，不能重复叠加当作新overlay。vv PBB fallback才是当前真实二次代码改写。

## 推荐归并方案（待主线采用）

保留一个公共Pi/plugin core生产源与已有ordered patch清单，区分standalone和managed两种执行生命周期合同；不建立variant配方生成器、不相互importvariant，也不先拆成多份依赖产物。已有managed适配继续显式环境启用，公共mechanics修复只在共享patch维护。

在现有runtime-source中补最终去重target SHA（后续补丁后的字节）与native-managed SHA；统一builder输入guard核当前npm lock/ordered patch身份、最终target字节及模块，再采用已验证runtime。现有I15 patch身份和retry字节guard可归并到该支持边界，vv catalog exactguard由完整baseline guard覆盖。机制包括现有通用修复，不让variant临时补一个error分支。vv删除PBB旧fallback，只消费baseline；source仍记录实际baseline与执行适配身份，旧runtime应明确拒绝而非自动原地打补丁。

Dockerfile patch命令由现有native_patch_specs生成进入其临时构建context，只去掉手写顺序重复，不生成Harness。角色/技能/模型/业务语义以及compaction数值配置留在各实际owner；system/tools通用边界需以共享patch维护。catalog开关当前保持明确launcher启用，是否改为插件默认能力需单独确认所有实际role消费者的可见范围，不能只靠两父prompt成功推断所有caller。

验证复用编译、真实producer物化、完整目标身份与无模型原生ExtensionRunner输入构造；已有真实PBB/SDK操作证据按source身份采用。managed实际启动/取消/收尾沿所属真实执行合同取证，不以standalone drain代替。禁止Factory/Braid测试、包smoke和新付费run。旧冻结包/当前官网完全不动。

## 判别未知与下一步

本轮静态清单证明当前源归属和已存在的消费路径，尚未生产新的统一baseline产物、没有证明I14历史包当前所有bytes一致；后续迁移不可宣称它们已升级。重复29suite启动/wait误用需结合实际工具回执判断是模型重开、服务生命周期误标，还是通知/handle缺陷；仅共享prompt改写不能宣称该问题根治。主线采用方案后，再由同owner实现manifest/guard与vv去overlay，受支持活动Braid消费者接共同guard，真实物化后报告各消费者实际选材，不修改生成业务应用。

## 已采用并实施的有限归并

公共producer增加 apply_native_patches/native_baseline_manifest/require_native_baseline，复用既有patch清单，记录51个去重最终目标字节；Linuxcontext生成同顺序shell文件，Docker只执行该文件。derive-linux核冻结targetmanifest而不靠补填旧字段。vv已删除PBB legacy二次改写并使用完整guard；I15用同guard，覆盖目标与runtime-source实际baseline metadata，仍保持Braid binary和资源helper合同。standalone/managed模式明确记录，角色/模型没有归并。旧pi-minimal仅撤维护推荐，源码与已有guard保留，I14未迁移。

实际生产证据见 singlephase-20261008/pi-baseline-production-20261008：当前锁定原npm包应用全部14补丁（zero fuzz）后写manifest，51targets真实物化，vv copy与I15实际builder目标选材相等；旧e2e runtime具体拒绝，当前新stage通过；新插件实际ExtensionRunner加载PBB/subagents errors=[]、catalog仅advisor metadata，没有模型。stage是实际Pi/plugin目标产物，不是完整可交付Linuxruntime，完整runtime/包未重建，官网未部署。五个下载包有lock SRI并校验，nested pi-ai锁未给SRI，保存下载SHA/精确version，实际patch后的retry字节另按既有锁定SHA核定。

## PBB 与 wait 的新证据边界

peer对d37冻结字节和调用已证明：PBB批处理补丁已带入；subagent_wait(id)只核subagent命名空间，传bg句柄却返回正常Nothing to wait for；PBB完成后从active移除，Agent忙时排入completion队列，agent_end才flush。工具循环turn_end不是agent_end，故持久完成结果暂时不可见，aggregate等provider消失不等于拿到完成正文。shell管道/tail掩Node非零是shell退出值，PBB如实采集shell结果。当前统一baseline不改此事件调度或跨provider命名。后续可单独采用明确错误句柄类型拒绝及已有持久结果取回能力的机械修复，不能通过扩大prompt承诺消除重复任务。
