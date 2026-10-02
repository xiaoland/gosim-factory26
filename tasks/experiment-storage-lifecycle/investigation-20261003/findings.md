# 实验空间增长排查

2026-10-03，用户要求排查“为什么每次进行实验都需要吃掉至少10GiB的空间”。本轮只调查磁盘和当前生产链，不修改设施源码、不清理历史、不运行模型或设施测试。原始目录已被另一授权任务清理，现存样本是 I13-2 及其恢复、监控与重放材料；不能据此证明每次独立实验都至少新增 10 GiB。

## 当前证据

`local-du-k.txt` 是 `du -k -d 1 runs/iteration13/i13-2-20261001` 的完整输出。该目录累计计量为 167.49 GiB，包含多个平台 run、准备尝试和恢复，不是一条 run 的成本。最大的两个子目录为 `hosted-github-self-funded-r4` 53.86 GiB 和 `hosted-sheet-r2` 52.66 GiB。其后是 preservation 8.77 GiB、revision2 8.56 GiB、experiment 7.24 GiB、arc-hot-recovery 6.58 GiB。上述一级目录不互相包含，但 APFS clone 可能共享底层块，不能相加宣称独占物理空间或可释放量。

Sheet 的 monitor 单独计量约 52.13 GiB。其中 105 个 `workspace.zip` 的逻辑大小合计 28,700,418,587 bytes（26.73 GiB），包括一个零字节失败下载；其文件占块计量合计 28,700,643,328 bytes。余下约 25.40 GiB 属于提取证据及索引等，未逐类拆账。105 个 ZIP 分属三个平台 run，不能说一个 run 下载了 105 次：

| 平台 run | ZIP 次数 | ZIP 累计 GiB |
| --- | ---: | ---: |
| e1aa595f6995 | 65 | 17.80 |
| f16834f58674 | 20 | 2.95 |
| 7e8ec62670df | 20 | 5.98 |

这是直接可观察的重复全量采集。`lab/arc_bench/hosted_monitor.py:218` 每轮传 `with_workspace=True`；`:167` 下载完整模板 ZIP，`:175–180` 从中提取 `.factory26` 状态与原生证据并另行保存。历轮 ZIP 和提取的证据都留下。每个 ZIP 在写入时包含当时全部历史，而非本轮新增。监控的磁盘成本因此随采集次数增长，历史证据本身增长又会使后续单轮更大。这里测量的是旧 ARC collector；新 `lab/exp/hosted.py` 的 platform JSON 导出不能据此被称为相同的完整 workspace 轮询。

源数据见 `monitor-zip-sizes.json`、`sheet-monitor-by-run.json` 和 `sheet-monitor-batches.json`。只读取 status 的身份、状态和时点，不读取原生 rollout 正文。没有对全部 ZIP 重算 hash。

## 当前源码仍存在的空间倍增

| 生命周期 | 当前行为 | 成本归属 |
| --- | --- | --- |
| 启动材料 | Runtime 包含 Node 依赖、Chromium、动态库和字体。样本 package-stage/runtime 约 1.07 GiB，其中 node_modules 约 412 MiB、Playwright 约 384 MiB。 | 按 runtime/material 身份共享的基础资产，不应每次算新成本。 |
| 发布材料 | `environment.py:175` 将 producer cache 的 payload 发布；`artifacts.py:214` 普通完整复制到 store。Hosted ZIP 同时保留 cache 和发布副本。 | 首次生产多个物理载体；以后相同 production index 可复用。 |
| 输入装配 | `controller.py:561–563` 为非 Docker attempt 完整 materialize；`artifacts.py:325` 普通 copytree。 | 每 attempt，包括重试。 |
| 终态保全 | `runner.py:596` 复制 workspace 到 terminal-evidence；`:604` publish 又复制一份；`:558` 独立发布 named outputs。 | workspace 原件、终态 staging、终态 artifact 至少三处完整现场，另叠输出。 |
| Docker 回传 | `backends.py:558–570` 拉取完整 execution 到 payload-export stage，再复制 workspace 到本机 attempt；成功保留 stage。旧 SDK `docker_workspace.py:315–323` 则保留未压缩 tar 再解包。 | volume、回传载体、接收现场并存，随后还会叠终态发布。 |
| 热恢复 | `exp_checkpoint.py:471–478` 捕获整个 source 和材料，`:520` 完整派生 prepared；publish 和 runner 工作区装配再复制。旧交付包还嵌入 recovery ZIP 及完整基础 runtime。 | 每 checkpoint、prepared 和恢复 attempt；恢复继承的历史也进入下次全量捕获。 |

新 DX 的正式环境路径已经通过 `controller.py:248–260` 将 run/artifacts 链接到环境共享 store；controller 与 runner 也共用一个物理 Python runtime。不能将符号链接或两份用途回执算作两份资产。这些已有改进并未消除 workspace、输运和终态阶段的完整复制。

`artifacts.publish` 按 publication request 幂等，不按 payload 内容去重。不同 request/provenance 可以保留同内容的不同 artifact，也会复制其 payload。生产者身份分离是正确合同；物理存储复用尚未随所有生命周期贯通。

Checkpoint/material 的部分复制已经使用 Darwin clonefile。同卷 clone 的逻辑完整副本不等于完整新增块；Linux、跨盘、Docker 输运及普通 copytree 不能沿用这个假设。12 GiB storage reserve 只是门槛，并非预先写入 12 GiB；降低门槛不解决上述复制。当前 runner 还显式要求 `reserve + 2 * evidence_size + output_size` 的终态余量，复制已进入容量需求。

## 判断与下一轮改进方向

10 GiB 不是每实验不可避免的底座。观察支持两个主要原因：监控持续保存全量快照；不同执行阶段为自己的完整性边界各自复制完整现场。数 GiB 的输入或 workspace 经过三四次复制就超过 10 GiB，尚未算远端 volume、镜像层、失败 partial 与重试。

首先应让监控保存每轮必要的身份、状态、告警与增量证据；完整现场只在明确恢复点、终态或故障取证时封存。若平台只提供完整 ZIP，下载成本与永久保留成本要分开处理，不宣称本地去重已经减少网络请求，也不能直接删除原文而失去可恢复证据。

其次应区分可执行共享资产、可写 workspace、恢复点与只读归档用途。恢复应引用冻结 runtime/material，加上该时点真正需要的可变状态；不能因为完整 source 捕获方便，就反复把材料和既有恢复历史带入新现场。实际保全范围必须由 Harness 语义确认，不能从 node_modules 或缓存目录名直接判断可删。

然后应贯通封存、发布和接收：完整 payload 获得一个受管物理载体，artifact/attempt/来源关系保持独立。支持的同卷位置可用 clone；已经封存的载体可在有明确所有权及耐久性边界时被发布消费，不必先 staging 再 store 完整复制。不同身份指向相同物理内容不要求改成万能 trace ID。输运成功后的可重建 scratch 与源证据也需分别保留，而不是永久等量归档。

验收应分别计量首次冷资产成本、相同环境的新 run 增量、一次恢复增量，以及打包/启动/回传/终态的峰值 scratch；同时记录字节、占块口径和耗时。不以清理旧目录后空闲增加作为生产链优化验收，不以单次 du 证明 APFS 独占块。这轮没有测量远端 Docker volume 或镜像的实际增量，也没有新运行取得上述验收。
