# I14 E2E 变体导航

E2E 在 I14 基线上增加独立冻结的 E2E 工具 runtime。普通入口仍是 [`main.py`](main.py) → [`run.py`](run.py)；工具 addon 先由 [`tools/build-e2e.py`](tools/build-e2e.py) 生成，再由 [`build.py`](build.py) 或 `run.py` 以 `--e2e-runtime` 接入。

## 改什么看哪里

- E2E 依赖、Linux addon 和来源回执：[`tools/build-e2e.py`](tools/build-e2e.py)；它要求显式输出/cache，禁止消费标记为 superseded 的 addon。
- E2E CLI 和 MCP 接线：[`tools/e2e-cli`](tools/e2e-cli)、[`tools/mcporter.json`](tools/mcporter.json)。
- 测试配置、浏览器和输出目录：[`tools/e2e.config.ts`](tools/e2e.config.ts)；运行时环境和 daemon 清理：[`run.py`](run.py) 中 `E2E_RUNTIME`、`e2e-daemon-cleanup.json` 相关段落。
- 反馈：查看 E2E 运行输出、trace、控制台/请求错误和 `e2e-daemon-cleanup.json`，再与应用交付回执分开判断；E2E 检查不改变 Lab experiment 状态。

E2E 是额外工具材料，不是把 `agent-browser` 替换成新的通用运行入口；未准备有效 addon 时 `build.py` 会拒绝打包。源码核对：[`main.py`](main.py)、[`run.py`](run.py)、[`build.py`](build.py)、[`tools/build-e2e.py`](tools/build-e2e.py)。
