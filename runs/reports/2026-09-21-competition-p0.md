# 参赛 P0 适配与无模型验收

本次完成 Python ZIP 入口、frontend/backend 部署契约、Linux 运行制品与隔离、平台模型配置注入四项 P0。实现前方案提交为 `bc8450b`；没有模型调用、平台上传、正式评测或 Git push。操作说明归属 [运行文档](../../docs/deployment/index.md#参赛包与平台边界)。

## 制品与来源

| Backend | 本地 ZIP | 字节数 | SHA256 |
| --- | --- | ---: | --- |
| Pi | [factory-pi-p0.zip](../packages/factory-pi-p0.zip) | 96,435,197 | `b20a4e9fc83b7ff8435d6986aafb291f989090611d8cb7d1eeab8eb9f122762c` |
| Codex | [factory-codex-p0.zip](../packages/factory-codex-p0.zip) | 348,262,481 | `4909fb542923ca4e4e7ff2cf48d9bc370e49599c2d6ac47b03ca349d0765994a` |

两份包分别包含 13,963 和 12,563 个载荷文件。独立核对了清单 SHA256、ZIP 无符号链接、空 requirements.txt，以及入口和六个运行脚本与当前源码一致。包内不包含评测器、测试脚本、旧生成应用或密钥。Braid 与 SVC 源码身份、Node/npm/Python 依赖身份在包内清单和 lock 文件中保留。ZIP 与原始检查日志位于被 Git 忽略的 runs，不随源码提交。

## 验收证据

Mac 与原生 x86_64 Linux 分别执行 81 项单元检查，各跳过 1 项另一平台专属检查；互补覆盖 macOS sandbox-exec 与真实 Linux Landlock。Linux 验证孙进程继承限制、宿主标记读拒绝、需求可读且写入/删除/替换拒绝，以及符号链接不能绕过限制。

两份最终 ZIP 在非 root（UID/GID 1000）、1 CPU、2 GiB、Docker network=none 下分别完成 [入口验收脚本](../../tests/submission_smoke.py)。容器使用 CPython 3.12、系统 Node 20.19.3 和 Git；Harness 自带 Node 22.22.3。内核实测 Landlock ABI 7。真实 Pi/Codex、Braid、SVC 与 npm 均在文件隔离内启动，SVC Corpus 可读取；Pi 的自定义模型配置可被核心列出。Codex 路径还真实启动 LiteLLM、检查健康状态并正常停止。

完整交付部分显式使用测试专用 Braid 替身，生成一个无依赖网页并返回固定 Git 提交及模拟原生会话。它验证了真正的 main.py 参数与环境接入、隔离预检、Git 导出、原生证据归档、平台目录保护、标准安装/构建/启动、HTTP 页面响应和非零退出。独立需求目录、output/requirements 输入、重复交付拒绝及失败 delivery.json 均经过检查。替身仅修改测试解压副本，结束时恢复二进制与清单并重新校验；不在参赛 ZIP 中。该检查不证明真实 Braid 调度、模型推理或应用质量。

凭据回归确认不读取开发者 key，配置不保存密钥；Codex 适配器也只继承白名单环境和所选凭据。Playground 新上传需显式选择练习，续跑/启动/取消在网络请求前拒绝未知或正式 ID。文档链接检查通过，SVC status 为 healthy。

原始证据：[检查摘要](../p0-acceptance/summary.json)、[制品摘要](../p0-acceptance/packages.json)、[Mac 检查](../p0-acceptance/mac-tests.log)、[Linux 检查](../p0-acceptance/linux-tests.log)、[Pi 入口](../p0-acceptance/pi-smoke.log)、[Codex 入口](../p0-acceptance/codex-smoke.log)、[容器限制](../p0-acceptance/container-config.json)。

## 尚未验证

官方公开模拟仓库版本为 `cfbbc287ee1bbffcf1e936545e4803145693a8d8`，其生产 Runner 源码和可拉取镜像地址没有随包发布。本次验收容器采用 Debian Bookworm，不是其声明的完整 Ubuntu Noble 生产镜像；生产内核/seccomp 是否允许 Landlock、完整工具链和联网依赖安装仍需正式环境验证。生产平台 ZIP 大小上限未知，尤其 Codex 包约 332 MiB。真实模型生成与正式平台提交尚未运行，不能把这份报告视为线上兼容性、参赛资格或正式成绩证明。
