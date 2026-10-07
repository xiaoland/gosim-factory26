# 代码与组件边界审计

审计时间：2026-10-07。范围是当前工作树的实际入口、导入、装配和冻结消费者；未运行构建、测试、模型或服务。结论只回答哪些边界值得先收敛，不把静态未引用当作可删除证明。

## 1. Console 根目录混合了两个真实产品面，优先拆“认知边界”，暂不合并源码

观察：新 run 的服务入口是 `python3 -m lab serve --config FILE`。`lab/serve.py:1-35` 创建共享 Backend、OTLP 接收器和投影线程，`lab/serve.py:63-67,118-133` 直接消费 `sources.braid.viewer.reader` 生成和读取 Braid projection；静态前端由配置的 `static_root` 提供（`lab/serve.py:135-149`）。当前前端源码仍位于 `braid-console/web/`，其 README 将 `RunOverview`、运行摘要、Braid 页面和 API 类型列为当前页面（`braid-console/README.md:1-3`、`braid-console/web/README.md:16-27`）。

同一个 `braid-console/` 根下的 Python `service.py/server.py/archives.py/docker_runtime.py` 则是旧冻结 Console。README 明确标为旧 schema1 服务（`braid-console/README.md:5-11`），旧制品仍通过 `service.py prepare` 冻结 `service.py`、`server.py` 和 `web/dist/index.html`（`braid-console/service.py:42-62,210-245`）。这条链不能按“新 Console 已替代”直接删掉。

但这里存在一个可直接处置的生产边界问题：`service.py prepare` 会无条件把当前 `web/dist` 打进旧 Python server；当前 `App.tsx` 已切换到 `RunOverview`，其请求包含 `/api/runs/:id`、`/resources`、`/logs`、`/cost`、`/evaluations` 和 `/braid`（`web/src/RunOverview.tsx:23-27`），而旧 `server.py:268-331` 只提供旧的 query-string `/api/runs`、`/api/items`、`/api/item` 等接口。静态接口对照显示当前源码产生的新 UI 与旧 API 不匹配；本轮没有启动旧服务，不能把它表述为已实测的部署故障。

建议：保留 `braid-console/web` 作为当前 Console UI 来源，保留旧 Python 源码作为兼容实现，但先把 `service.py prepare` 视为旧 UI 制品入口而不是当前 `web/dist` 的通用打包器。最小处置候选是让旧生产链消费一份明确的 legacy UI 构建输入，或在没有该输入时拒绝 prepare；这需要确认是否仍有用户要求重新准备旧服务。未确认前不删除旧 Python 源码，也不把当前 UI 继续宣称为旧服务兼容 UI。

当前工作树还有一个可确认无效的源码入口：`App.tsx:1,11` 仍导入并懒加载 `BraidRun`，但当前渲染分支只使用 `RunOverview`（`App.tsx:44-49`）。`tsconfig.json` 未开启 `noUnusedLocals`，因此这不会被静态检查暴露；可以删除 `App.tsx` 中未使用的 `lazy/Suspense` 导入和 `BraidRun` lazy 声明。现存 `dist` 的 `BraidRun-*.js` 可能来自旧构建，不能据此判断当前源码仍会发出它。`BraidRun.tsx`、`Review.tsx`、`Discussion.tsx` 等 Braid Console 产品源码仍保留为待恢复的独立构建/入口候选；当前 Lab Console 未挂载它们，不足以推出可以删除。

共同杠杆是构建输入和入口说明，而不是合并 `lab/serve.py` 与旧 `server.py`：两者一个读取新 run manifest/OTLP，一个核对旧 service manifest、Docker 身份和人工接入权限，合并会扩大权限和生命周期耦合。两个实现可以未来放在同一 `console` 父目录下，但内部源、制品 ABI 和服务生命周期仍应分开；“不同生命周期”本身不构成必须拆一级目录的理由。

## 2. `sources/braid/viewer` 是 Console 的实际读取依赖，应保持为独立组件

观察：新 Console 的 materialize、projection 和 artifact page 都从 `sources.braid.viewer.reader` 导入（`lab/serve.py:63-67,118-130`）；离线诊断页面也直接导入同一 reader（`lab/analysis/braid_telemetry_viewer.py:15`）。这不是 Console 自己的重复实现，而是 Braid 源码提供的读取投影能力。

建议：不要把 `sources/braid/viewer` 搬入 `braid-console`，也不要因 `braid-console` 负责展示就删除 Braid viewer。更合适的收敛动作是把“Braid viewer 是共享读取组件、Console 是消费者”写进组件索引，并在未来冻结其 reader 输入/输出合同。只有在确认旧归档、离线 viewer 和新 Lab serve 全部切换到新稳定接口后，才有理由改物理归属。

## 3. 当前 `lab` 与兼容 `lab.exp` 是两条有意并存的执行合同，不能合并或删除 `lab.exp`

观察：当前公开入口 `lab/__main__.py:7-83` 只注册 run 级 `start/stop/pause/resume/restart/status/wait/logs/evaluate/archive/serve`；`lab/README.md:1-26` 明确新 run 不使用 experiment/job/attempt 控制器。与此同时，`lab/README.md:32-39` 把 `lab.exp` 定义为旧冻结执行的兼容入口，`lab/status.py:1-5` 和 `lab/exp/history.py:1-24` 仍读取旧 `lab.run`/experiment producer facts。

更强的消费证据来自旧 Console：`braid-console/docker_runtime.py:200-227` 为 schema 1–3 的旧 experiment 调用冻结 runtime 中的 `python -B -m lab.exp.controller internal_observe`；`braid-console/docker_runtime.py:240-246` 对新旧 schema 分别执行 access/query。公共制品冻结也把 `lab/exp` 的 collector、state、artifacts 等文件纳入支持闭包（`scripts/package_agent.py:350-357,442-467`）。因此“新入口已是 run”不能推出 `lab.exp` 无消费者。

建议：保留两个包名和旧 import ABI；先在 `lab/README.md`、docs 索引和组件地图中把 `lab` 标为当前 run 控制，把 `lab.exp` 标为冻结 experiment/attempt 兼容执行器。未来若要删除或重命名，必须先有旧 Console 制品版本迁移、冻结包重建策略和旧 schema 读取回归证据；当前缺少这些事实。

## 4. 公共装配、Linux 支持和材料保留内部边界，可以收拢物理目录

观察：`scripts/runtime.py:245-270` 在宿主侧创建 Docker staging context，把 `submission/Dockerfile` 与 `submission/build.py` 放入构建上下文，把材料 lock 复制为上下文内 `harness/npm`，可选 Braid 源复制为 `sources/braid`。这说明 `submission` 是容器内 Linux runtime 的构建/恢复实现，`scripts` 是宿主装配器，`harness` 是构建输入材料。

另一个冻结链证明它们不能简单合并：`scripts/package_agent.py:227-245` 把 `submission/exp_checkpoint.py`、`recover_completed.py` 和 scripts 支持模块分别复制到制品；`scripts/package_agent.py:330-357` 又分别记录 variant、runtime、skills、scripts support、submission checkpoint、Lab collector 和 gateway catalog 的身份；`scripts/package_agent.py:447-467` 在 readback 后再次按这些边界复制文件。它们是不同的来源身份和更新触发条件。

`harness/README.md:1-20` 的实际内容是 npm lock/patch、skills、依赖锁、gateway catalog 和 model recipes；消费者分散在 runtime、packager、Dockerfile 和 model proxy。由此，“harness”是目前最不精确的一级目录名，建议下一阶段优先评估 `harness -> materials`（或 `runtime-materials`）。迁移必须覆盖 `scripts/runtime.py` 默认 lock 路径、`package_agent.py`/gateway/catalog 路径、Docker COPY、variant 命令与材料 README；交付包内部的 `skills/`、`support/`、`harness-layout.json` 合同名不应机械改名。

建议保留 `scripts` 与 `submission` 的内部边界，并可将它们归入一个 `tooling` 父目录以减少一级目录。迁移消费者已明确：`scripts/runtime.py:245-270` 的 Docker staging、`scripts/package_agent.py:227-245,330-357,447-467` 的冻结/readback、`lab/exp/controller.py:34-43` 的源码闭包、各 variant 的 `from scripts...` 导入、Dockerfile 的构建上下文，以及文档中的命令路径。父目录只收拢物理位置，不合并内部职责或交付 ABI。`submission` 若进一步改名为 `runtime-image`，还会触及恢复入口和历史包 ABI，可作为后续独立迁移。

## 推荐处置顺序与缺失事实

1. 先处理 Console 的生产输入不一致：确认旧服务是否仍需重新准备；若需要，补齐或恢复 legacy UI 构建输入，若不需要则收紧旧 prepare 的使用边界。确认当前 UI 稳定后，删除 `App.tsx` 的未使用 lazy 入口，保留 Braid Console 产品源码。
2. 再把 `scripts` 与 `submission` 收拢到 `tooling` 父目录，按上述实际消费者一次性更新路径；不合并内部职责，也不改包内 ABI。
3. 最后评估 `harness -> materials` 以及 Console 两个面是否归入共同父目录；每项迁移保留实际消费者映射和旧制品入口，不把目录收拢扩大成源码删除。

会改变 Console 处置的事实是旧服务是否仍需重新准备，以及匹配 UI 的源码/构建输入能否取得。`lab.exp` 已有真实消费者，删除需要另行解决这些消费者，而不是由新入口存在直接推导。`harness` 的源码改名默认保留旧交付包、冻结记录和恢复合同的内部名称，不需要为目录整理改变它们。`App.tsx` 的未使用 lazy 入口已有静态清理依据，Braid Console 产品源码继续保留。
