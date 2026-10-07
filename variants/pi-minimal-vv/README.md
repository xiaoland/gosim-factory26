# pi-minimal-vv

独立的原生 Pi Harness：主会话默认 GLM-5.3-Flash，`--model glm-5.3` 可选择本轮另一个主模型；advisor 为 Kimi-k2.7-code，AI E2E 保持 GLM-5.3-Flash。独立提供 svc-verification 和 tester.army/e2e。生成、advisor 与 AI E2E 共用调用方注入的 API key 与端点；包不包含凭据。供应商次序由调用方传入的[跨 variant 模型配方](../../materials/model-recipes/README.md)选择并冻结，variant 不从 catalog 默认推断选路。费用模式和执行范围由所属任务授权；本地自费 API 不默认设置人为费用、时长或 idle 停止阈值。

在官方既有应用的 output 根增量工作，不清空或重建基线。每次启动在 `.factory26/pi-minimal-vv/runs/<随机run-id>/` 创建独立 HOME、原生会话、工具状态与证据；清理仍检查整个应用工作区的进程，但清理证据写入新 run。旧 `.factory26` 和根 `process-evidence` 不继续使用。 必要机械恢复可由执行负责人显式设置 `FACTORY26_PI_RESUME_RUN_ID`，仅复用已核实 variant、主模型与 session 文件的本轮原生会话；旧 result 和恢复身份另存，应用不回滚。正常启动仍创建新状态。该接口保留持久会话与应用，错误后的既有清理会结束本 run 服务和 E2E daemon，不能据此声称恢复了完整进程 checkpoint。构建时保证原生后台 Bash 的非交互错误终态不等待未完成任务，并将实际成员哈希记录在 runtime 身份中。

从现有 Linux runtime 派生纯 Pi 材料，保留冻结 e2e addon，删除 Braid 可执行入口；不预置应用源码、参考答案或业务原生依赖。main.py 拒绝 macOS 执行，Linux 的短 TMPDIR alias 指向本 run 的证据目录。

生产包可从冻结 runtime 使用 `tooling/scripts/runtime.py slim-linux` 派生浏览器精简材料。存在 `bin/browser-exec` 时，main 通过该入口使用平台浏览器或按需安装的浏览器；浏览器缓存归本 run 的证据目录。E2E 客户端保留独立 SDK，由 SDK 安装其兼容浏览器，不再硬绑定包内 `e2e/browsers`。旧离线 runtime 仍可使用 `bin/chromium`。采用精简材料前必须同时核对主 runtime 和 E2E addon 的浏览器目录，不能只裁掉一个 Chromium 入口而保留另一整份浏览器。

原生 Pi 以 `PI_OFFLINE=1` 运行，因此 Linux runtime 必须预先包含 `bin/fd`，供原生 `find` 使用；构建缺少该依赖时直接报错。`bin/rg` 只满足原生搜索工具，不能替代 `fd`。工具二进制及上游来源随 runtime 身份冻结，不依赖运行时下载。

调用方可通过 `TASK_CONTEXT_FILE` 提供 bench 冻结的附加任务材料。配置后必须是可读 UTF-8 文件，main 在模型调用前核实并在最终 prompt 中引用其路径；未配置保留原入口。任务专属正文由 bench 持有，variant 不内置。GLM-5.3 按本轮实际后备 API 的文本能力声明，原生 Pi 会明确提示图片未发送；不能仅因 read 工具支持图片就假定模型连接支持 `image_url`。

官网装配可给 `build.py` 显式传入 `--task-context-config <bench task.json> --task <task-id>`。构建复用公共 context helper，将材料与来源回执冻结在包内 `bench/`，以薄 `main.py` 绑定 `TASK_CONTEXT_FILE` 后执行原入口 `agent-main.py`；官方需求文件保持独立，不依赖官网额外注入该环境变量。未选择 context 参数时构建保持原入口。正式采用历史已冻结版本时，应从该版本与明确机械 overlay 装配并核对成员哈希，不能用当前工作树重建来冒称历史版本。
