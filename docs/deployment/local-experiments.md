# ARC 本地实验

本页维护 ARC run 的本地操作入口。重构实施与实际验收状态见[决赛设施 packet](../../tasks/finals-experiment-loop/packet.md)；旧 experiment schema 和 Runner 取证合同只用于对应冻结执行，见[历史本地实验合同](history/local-experiments.md)。

## 当前流程

配置好 target 和 task 后，在已有模型授权范围内用三个参数启动，复杂顺序使用普通 Python：

```sh
python3 -m lab start I14-dx-test wsl TASK
python3 -m lab status RUN --json
python3 -m lab wait RUN --json
python3 -m lab restart RUN --keep-data --task NEXT_TASK
```

新路径没有 compile/doctor/build 前置步骤、稳定 request-id 手工输入或容量预约。start 组装 program、输入需求与实际 target，保存采用的代码和配置。gateway/collector 的真实接线仍在设施任务验收；尤其 --route 已冻结但所读 DX 运行入口尚不消费路由文件，不能据此认为已启用自费链。运行自己的 observer 保存 status；查询不会另起现场采集。CLI/Console 关闭不影响执行。

公共程序入口在调用 Harness 前安装工具 Node、原生 npm 依赖及 variant 声明的 E2E 能力，本地和 Hosted 使用同一安装材料。操作者不需要先挂完整 runtime、切换预打包模式或手工接 E2E 路径。程序包携带锁文件、补丁和必要 Linux 库，不携带 Chromium 或预安装的 npm 依赖树；已有浏览器路径保留，需要下载时使用运行自己的可写缓存。安装失败从该 run 的实际日志定位，不能把平台启动受理或程序帮助输出当作安装与 Harness 工作均已完成。历史冻结包保持原安装方式，本轮实际覆盖见任务 packet。

应用正常完成后，默认 Python 程序冻结应用并启动 task 配置的 evaluations；四个评测入口分别是公开需求 simulate、题目自带 task、ArcBench 私有 self-test 和官网冻结应用 official。它们各有独立 run、工作区、来源、费用和结果。self-test 从源运行的 `github-stage-N` 自动选择 `github-stage-N-req-test`，使用同一冻结应用 ZIP，结果不计排名；它通过自测站的 upload-url、对象 PUT、submit/status 协议保存平台原件，不继承 Hosted `/submissions` 或模型路由。执行宿主使用自测站对应的 Helium 私有会话材料，不能把 Mac 绝对路径或 cookie 值作为远端输入。未配置的 simulate/official/self-test 不自动执行，官网模式必须显式 self_funded 或 competition。隐藏反馈不注入下一阶段。
远端生成的自动 self-test 请求由 Mac relay 接管：relay 先保存远端数据，再在 Mac 创建独立 child 并启动它自己的 observer/save；因此不会把 Helium 会话路径或 cookie 值写入 WSL/sfp7。只有显式配置远端 self-test target 时，装配器才通过私有 0600 文件传递已过滤的目标域 cookie。

## 执行位置与证据

WSL/sfp7 的执行位置、Docker、镜像、runtime、运行根目录及共享观测地址由 target 配置提供，不从 Mac 的路径或 loopback 猜测远端。Mac 控制和回收全部在 WorkSSD，远端数据允许保存在实际宿主磁盘。Hosted 使用平台身份及自包含包，不与本地容器句柄混用。

每个 run 保存整个 data/workspace 与 data/harness、日志、资源、遥测、费用和平台结果。stop 操作实际容器或平台 run，不据 Mac 控制进程退出宣称远端已停止；回收失败保留原错及远端唯一副本。pause/resume 使用 Docker pause/unpause，保留同一次执行；不保证释放内存或保住所有外部网络连接。

`restart RUN` 确认来源停止并保存现场后，从题目基线重新组装同 variant 的新 run，不继承进度。`restart RUN --keep-data` 才迁移 data：同 task/需求版本恢复原生会话，下一 task 新建原生任务状态，历史 data 与应用保留；旧 records、费用和隐藏报告不迁移。Python stages 显式使用 `keep_data=True`，不会因为默认值改变而丢弃上一阶段应用。当前源码与参数见 [Lab](../../lab/README.md)，范围和允许损失见所属 packet。

## 历史入口

旧运行的 schema、`host-lab`/旧 `lab run`、ARC-Bench workspace、raw Pi/Codex 基线和浏览器验收合同保留在[历史本地实验合同](history/local-experiments.md)，只用于解释已有原件，不能创建当前实验。
