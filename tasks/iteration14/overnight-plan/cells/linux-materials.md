# I14 Linux 材料生产回执

2026-10-03。用户最新授权自动实施及开工；本 owner 生产材料并扩展既有 producer 接缝，没有发模型请求、派发官网 run 或提交 Git。所有生产目录、临时文件、Cargo/Zig/npm/pip 缓存及日志实际位于 WorkSSD，材料与卷的 device 均为 `16777242`。

## 当前可消费材料

- `runs/iteration14/overnight-20261003/assets/runtime`：只从保留 I13 Linux ZIP 提取 runtime，保留 Node/npm 补丁来源，替换当前 Braid，并装配 `litellm[proxy]==1.102.0` 的 Linux x86_64/CPython 3.12 wheels。运行入口是 `runtime/bin/litellm`；pip 生成的 Mac shebang scripts 已删除。
- `runs/iteration14/overnight-20261003/assets/e2e`：锁定 npm 依赖按 `--os=linux --cpu=x64 --ignore-scripts` 安装；Playwright 1.63.0 下载 Chrome for Testing 153.0.8010.12、Chromium revision 1243 及匹配 Headless Shell。继承 Linux 浏览器库时读取实际 ELF DT_NEEDED、GNU 符号版本及哈希，闭包包括 98 个 ELF 对象，不仅按 SONAME 判断。
- `runs/iteration14/overnight-20261003/production-readback.json`：实际 Braid/浏览器及 Python wheel 平台、native ELF、GLIBC 版本与物理设备读回。Linux native 操作尚待已授权官网首轮，不能把静态材料反馈称作动态加载/e2e 通过。

Braid 来源 HEAD 为 `83e723d002231331236128590b5c4b72e91067fe`，实际未提交源码单独绑定完整文件 inventory；source SHA256 为 `845c573d406dc559813823de6a119babf592da7a92902b00c9ba23796a7f8da0`，binary SHA256 为 `c88d0941eefe19f4216a14f9122b8bb5c33ccc6068f48eb264d40b63b2451e27`。`cargo zigbuild --locked --release --target x86_64-unknown-linux-gnu.2.36` 实际成功，耗时 4m23s，11 条既有 dead-code warnings；ELF 最大 GLIBC 需求为 2.34。保留基础 ZIP SHA256 为 `7de33f7d23a910ec61e4b639275305cdd05222416ff01f2e757d55e58c1ff316`，原 ZIP 未修改。

实际生产命令：

```sh
PATH='/Users/lanzhijiang/.local/share/uv/tools/cargo-zigbuild/lib/python3.13/site-packages/ziglang:'"$PATH" PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime.py derive-linux --output runs/iteration14/overnight-20261003/assets/runtime --base-package runs/iteration13/i13-2-20261001/hosted-sheet-r2/agent.zip --braid-source sources/braid --cache-root runs/iteration14/overnight-20261003/cache
PYTHONDONTWRITEBYTECODE=1 python3 variants/pi-braid-i14-e2e/tools/build-e2e.py --output runs/iteration14/overnight-20261003/assets/e2e --base-runtime runs/iteration14/overnight-20261003/assets/runtime --cache-root runs/iteration14/overnight-20261003/cache
```

日志归 `cache/logs/{braid-build,router-dependencies,e2e-install}.log`。一次 Cargo 旧 git cache 的断链导致复制失败；该项目只需 registry，因此停止复制无关 git cache 并删除本次部分副本，基于已完整提取的来源恢复生产。e2e 收集曾错误地将 JS esbuild wrapper 当 ELF，随后缩到实际 Linux 二进制；静态 Go esbuild 没有 `.dynamic`，按其实际静态属性处理。没有建设远端域或运行模拟测试。

## Producer 接口

`package_agent.selection/plan_material/produce/package` 及 CLI 新增末尾可选 `provider_env`/`--provider-env`、`application_seed`/`--application-seed` 与 `gateway_routes`/`--gateway-routes`。provider_env 是当前激活链的明确私有 JSON 字典或 `{environment: {...}}`；gateway_routes 是公开 alias→有序 deployment ID list，写为 `support/gateway-routes.json`，不依赖 Hosted 注入路由环境。选定私有输入必须恰好提供本链 catalog 引用的 api_base/api_key 环境变量，不能夹带其它秘密或缺启动配置。application_seed 仅 reviewer 可用，消费 published application manifest v2 的目录或 ZIP，具体 seed 导入仍归 experiment_evidence。

公有 material identity 绑定输入的实际 hash/mode，不写凭据内容。模型私有配置在 `.private/provider-env.json`（0700 目录、0600 文件），与工具凭据共存；完整 ZIP 为私有制品。support 装配 `hackathon_gateway.py`、`hackathon_gateway_compat.py`、`responses_compat.py` 和 `model-gateway.json`。provider owner 持有 gateway 启动及各 build.py 私有参数，主 Agent 持有首轮 run 接线和唯一派发。

`lab/exp/environment.py` 的 material 路径解析/白名单已消费新增三输入，保持现有布局及 checkpoint v3。e2e build 已接入公开路由和私有环境；reviewer build 由 seed owner 接相同参数。材料生产与 host-exp 的 uv/pip/npm/temp 新写入使用既有 producer 的 WorkSSD 环境；不改变定义/state 职责。五个本 owner 源码完成 Python 编译，编译输出在 `cache/compile`。完整私有包生产及读回已完成；平台动态加载与实际请求由首轮官网反馈取得。

## 首轮真实私有包

入口 owner 确认源码稳定后，使用上述 runtime/e2e 及 provider 的 stage-a 公共路由/选定私有环境完成两次真实生产。初次包的直接原生边界核对发现 DeepSeek 的新 provider 别名未进入 strict modelScope 白名单；主 Agent 用现有 `bind_native_model_scope(settings, routes)` 修正。初次版本保留为 `stage-a/agent.before-model-scope.zip` 及 `package-held.json`，从未派发，不消耗模型实验机会。

最终产物为 `runs/iteration14/overnight-20261003/stage-a/agent.zip`，SHA256 `c54822b3821e661d8712e10e5978f117399e80689cd92e02e34f72e809fcfa1b`，883,254,528 bytes；material ID 为 `material-591f24eab7a9aeb4e63bb30778fe15a4a1644484ea18bb71125c6d6a54bf4446`。ZIP/父目录为 0600/0700，device 与 WorkSSD 一致。全部 45,030 条 archive entry 的实际内容、清单哈希和执行位读回完成；私有条目为 0600。公共路由与选定的 8 个 provider 环境引用一致，工具私有配置只含 Context7/Exa 两字段；Braid 编译 SHA、Linux Node/Chrome/Headless/esbuild ELF、Braid owner 预算及新的 modelScope 映射已读回。

`.secrets/legacy-home-config/llm.env` 实际只含历史 Factory API key，`.secrets/models.env` 没有两工具字段，因此本次只从保留 I13 ZIP 的 `.private/tool-env.json` 读取两个已授权工具字段，写入 stage-a/tool.env（0600）；不复制其余秘密。官网主 credential 文件为 `stage-a/.private/hosted-qianfan-flash.json`（0600，`api_key` 字段），这里只记录路径，不记录值。

真实操作命令：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/package_agent.py --variant pi-braid-i14-e2e --runtime runs/iteration14/overnight-20261003/assets/runtime --e2e-runtime runs/iteration14/overnight-20261003/assets/e2e --provider-env runs/iteration14/overnight-20261003/stage-a/.private/provider-env.json --gateway-routes runs/iteration14/overnight-20261003/stage-a/support/gateway-routes.json --tool-env runs/iteration14/overnight-20261003/stage-a/tool.env --cache-root runs/iteration14/overnight-20261003/material-cache --output runs/iteration14/overnight-20261003/stage-a/agent.zip
```

实际包回执为 `stage-a/package-receipt.json`，公开清单读回为 `stage-a/package-manifest.readback.json`。已交给主 Agent 直接消费；本 owner 没有模型、官网、测试或 smoke 调用，动态平台反馈仍由首轮取得。
