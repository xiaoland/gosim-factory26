# pi-minimal-vv-tailwindcss

独立的原生 Pi Harness：主会话默认 GLM-5.3-Flash，`--model glm-5.3` 可选择本轮另一个主模型；advisor 为 Kimi-k2.7-code，AI E2E 保持 GLM-5.3-Flash。独立提供 svc-verification 和 tester.army/e2e。生成、advisor 与 AI E2E 共用调用方注入的 API key 与端点；包不包含凭据。供应商次序由调用方传入的[跨 variant 模型配方](../../materials/model-recipes/README.md)选择并冻结，variant 不从 catalog 默认推断选路。费用模式和执行范围由所属任务授权；本地自费 API 不默认设置人为费用、时长或 idle 停止阈值。

在官方既有应用的 output 根增量工作，不清空或重建基线。每次启动在 `.factory26/pi-minimal-vv-tailwindcss/runs/<随机run-id>/` 创建独立 HOME、原生会话、工具状态与证据；清理仍检查整个应用工作区的进程，但清理证据写入新 run。旧 `.factory26` 和根 `process-evidence` 不继续使用。 必要机械恢复可由执行负责人显式设置 `FACTORY26_PI_RESUME_RUN_ID`，仅复用已核实 variant、主模型与 session 文件的本轮原生会话；旧 result 和恢复身份另存，应用不回滚。正常启动仍创建新状态。该接口保留持久会话与应用，错误后的既有清理会结束本 run 服务和 E2E daemon，不能据此声称恢复了完整进程 checkpoint。构建时保证原生后台 Bash 的非交互错误终态不等待未完成任务，并将实际成员哈希记录在 runtime 身份中。

从现有 Linux runtime 派生纯 Pi 材料，保留冻结 e2e addon，删除 Braid 可执行入口；不预置应用源码、参考答案或业务原生依赖。main.py 拒绝 macOS 执行，Linux 的短 TMPDIR alias 指向本 run 的证据目录。

原生 Pi 以 `PI_OFFLINE=1` 运行，因此 Linux runtime 必须预先包含 `bin/fd`，供原生 `find` 使用；构建缺少该依赖时直接报错。`bin/rg` 只满足原生搜索工具，不能替代 `fd`。工具二进制及上游来源随 runtime 身份冻结，不依赖运行时下载。

调用方可通过 `TASK_CONTEXT_FILE` 提供 bench 冻结的附加任务材料。配置后必须是可读 UTF-8 文件，main 在模型调用前核实并在最终 prompt 中引用其路径；未配置保留原入口。任务专属正文由 bench 持有，variant 不内置。GLM-5.3 按本轮实际后备 API 的文本能力声明，原生 Pi 会明确提示图片未发送；不能仅因 read 工具支持图片就假定模型连接支持 `image_url`。

本变体要求生成 Agent 将既有替代工具类方案迁移到 Tailwind CSS，同时保留业务行为、布局、框架和数据。实际构建与页面计算样式用于确认迁移完成，不能仅更换依赖名称。官方 Evolution GitHub 基线已经使用 Tailwind CSS 4，因此本题主要验证增量实现；无实际迁移对象时记录这一事实。原 pi-minimal-vv 不随本变体修改。

本轮官网下载的是本队 Stage3 `d86b43e8c891` 的 GitHub 上榜应用，并非共同官方参考应用；主线已核其 51 个 frontend/backend 源文件一致，官网下载物还带业务数据库。原有 Tailwind 4.1.18、`@tailwindcss/vite` 插件与 CSS 导入实际存在。本轮未授权原 vv GitHub 对照，不能将本题与 Sheet 的分数或耗时差异归因于样式迁移。

本地 Docker 调用方应启用 `--init`，由 init 回收浏览器和后台服务留下的孤儿子进程；仅用 Python 生成编排作 PID 1 可能积累僵尸进程并耗尽 pids 上限。2026-10-07 GitHub 本地运行实际触碰 512 上限，造成网关 DNS worker thread 创建失败；本次容器以 Docker 支持的资源更新提高至 2048 保留进度，未来启动同时启用 init。提高上限不是已回收当前僵尸进程的证明，也不是费用、时长或 idle 停止阈值。执行身份与原错见所属任务的 `execution.md`。
