# I13 工具接线实施

2026-10-01 最终检查更新：用户已修正 `.env.i13-tools` 中的 Exa key。主线通过当前 Pi SDK 装载本扩展，真实 `exa_search` 和 `exa_contents` 均返回 HTTP 200，request ID 分别为 `e3df760b2149abc6c823561538f085a3`、`0b51ab645155d73876fc2e595907eafd`。原始结果在 `runs/iteration13/final-readiness-20261001/exa/`；没有调用模型。下文 401 为原凭据的历史反馈，已不构成当前阻塞，最终私有实验包仍需装入修正后的值。

2026-10-01。范围来自用户已复核的 [工具与提示词方案](tools-prompts-plan.md) 和 [审计](tools-prompts-audit.md)。开工依据是用户：“我已经配置好了 .env.i13key。我复核了这份 tools-prompts-audit.md，没问题。你可以开工工具接线和Factory/Braid 提示词了。然后我们来讨论Braid 协作方法与 Requirements 树。”本页记录工具组；Braid 协作方法和 Requirements 树不在本组源码范围。

工作区起点与限定文件快照保存在 `runs/iteration13/tools-implementation-20261001/start/`，原始操作与构建反馈归同一证据目录。开始时已有大量其它任务修改；构建前提已单独提交 `a08070c`，收录此前已授权的 model-exclusion正文、必要构建引用与本次 GNU格式修正；它不算新工具功能。本组工具提交只收录起点之后的工具增量，共享 `run.py`、`runtime.py` 和 Git index 与提示词协作者串行协调。

## 实际接线

共用 npm lock 新增官方 `@upstash/context7-pi 0.1.2` 和 `@ff-labs/pi-fff 0.11.0`。Pi 装载器已经将 Typebox、pi-tui 的兼容导入映射到自身版本，因此没有新增重复 peer 声明。FFF 的 Node SDK及 Linux/amd64 原生依赖由锁定包依赖收录。

Context7 显式加载扩展文件及独立 `context7-docs` 技能，不加载包内 prompt 模板。窄补丁删除调用次数上限、强制重复 resolve 和固定选择/回答流程；有效 library ID 的前提归 `libraryId` 参数说明。错误保留 HTTP 状态、request ID（服务提供时）和有界原响应。技能保留来源选择、版本、公开查询和引用理由，其正文不进入 profile 或角色提示词。

Exa 使用一份原生扩展，注册 `exa_search` 与 `exa_contents`，通过 Node fetch 访问官方 search/contents API。参数包含必要查询、域名与发布日期筛选、结果数量、正文/摘录及缓存新鲜度；[官方 search](https://exa.ai/docs/reference/search) 与 [contents](https://exa.ai/docs/reference/get-contents) 是接口依据。每页正文/摘录限制默认 6000 字符，共享 30000 字符正文预算，返回来源 URL、原字符数和截断状态。错误保留 HTTP 状态、request ID及最多 8000 字符响应。没有新增 MCP 桥、克隆、缓存或模型抽取。

FFF 使用 `tools-only`，提供 `fffind`、`ffgrep`；原生 `find`/`grep` 保留，`PI_FFF_MULTIGREP=0` 不启用可选第三工具。补丁仅整理默认与可选工具的 metadata：去掉固定调用次数和工具优先流程，将参数语义留在 schema、检索语义留在 description。索引、分页、cwd 和工具执行行为沿用上游。

主 launcher 关闭自动扩展/技能/prompt/theme发现后显式加载。两份 profile 下的 explorer、executor加载 Context7/Exa及 Context7 技能；advisor、vision、browser-operator不默认加载这两项。FFF 与后台 bash 覆盖所有内部角色。child 的 `extensions` 也显式列出，继续禁用环境扩展继承。I13 mcporter 只移除 Context7/Exa，保留 Handsontable；其它 variant 没有改动。

## 私有凭据

实际输入文件是仓库根 `.env.i13-tools`；`.env.i13key` 不存在。该文件已由用户填写、Git 忽略且权限 0600。本组只读取这一显式输入，不复制、改名或读取个人配置，也不将 dotenv 当作 shell 执行。

`scripts/package_agent.py --variant pi-braid-i13 ... --tool-env .env.i13-tools` 将两个变量写到该次私有制品的 `.private/tool-env.json`，仓库内目标必须位于 Git忽略目录（默认 `runs/`），否则在写凭据前拒绝；目录权限 0700、文件权限 0600；含该目录的 ZIP 也为 0600，归档条目保留凭据文件权限。运行环境同名变量覆盖包内默认值，主/子进程继承同一环境。配置不进入源码、提示词、工具参数或共享日志。

## 已取得的反馈

Python源码编译通过。使用本次 lock 与补丁实际 `runtime.py prepare` 安装，然后由 Pi SDK 创建原生会话、发出真实 `session_start` 并执行工具，没有调用模型。FFF 在 I13 cwd索引 26 个文件，`fffind` 找到 run/main/build，`ffgrep` 返回 `native_files` 定义和调用。Context7 resolve React后 query-docs返回带官方来源的 useEffect cleanup 文档。

Exa 原生工具注册成功，但当前服务凭据被官方拒绝。search 返回 HTTP 401、`INVALID_API_KEY`，request ID为 `c67ce516c1c1199c57d248a0c8cde8bd`；contents同样返回 HTTP 401，request ID为 `99d28a16a168611a27314e3f563763a0`。原响应明确要求有效 key；原始错误在 `tool-operations.log` 和 `exa-contents-operation.log`。没有用其它凭据替代，也不能把这两次鉴权失败称为 Exa成功检索。

复用真实 GitHub requirements输入执行本次 source的 `prepare-only`，再通过 Pi原生扩展装载与 pi-subagents launch-contract材料入口取得两个主消费者和十种 child材料。十二处 extension errors均为空；Context7/Exa分配符合上述角色选择，全部保留 FFF 两工具及原生 find/grep，没有加载 multi-grep。最终冻结提示词后的材料入口是 `prepared-final/.factory26/20261001-010903-c133bd35`、`native-input-final/` 和 `role-tool-summary-final.json`；早期材料另外保留，不冒称最终版本。最终根任务不再带 origin/pnpm/portless稳定副本，child保持 append/fresh 与父 profile隔离。批量材料在同一进程反复装载十二份 FFF时产生 MaxListenersExceededWarning，原日志保留；单次原生会话的真实搜索未出现该警告。本地 runtime有明确 darwin-arm64身份，不能代表 Linux已验。

Linux完整链使用现有 `runtime.py linux --backend pi --docker-context arcbox-win --braid-source sources/braid`。前两次构建在已有 model-exclusion补丁的 GNU/BSD unified diff上下文差异处失败；原始失败日志和 reject已保留，提示词协作者将补丁重生成为标准三行上下文，保持行为和 `--fuzz=0`。第三次通过整条 GNU补丁链后，第四次使用冻结的最终提示词和工具源码再次完成构建，导出 `linux-runtime-frozen/`。本组将补丁应用移到浏览器安装后，避免仅改提示词补丁时反复安装浏览器；lock/patch身份在 Docker context复制后计算，Braid另记录复制源码身份，防止并行编辑造成版本误记。

最终 Linux构建包含 GNU原生 FFF依赖及 Braid release编译。将导出物的 Node和 node_modules复制到独立 Linux/amd64容器后，通过同一 Pi SDK真实 session_start装载三组工具，extension/hook errors均为空；`fffind` 返回3个文件，`ffgrep` 返回2处真实源码命中。该操作不含凭据，也不调用模型。证据为 `linux-frozen-build.log`、`linux-tool-operations.log` 和 `linux-native-operations/`，因此 Linux原生依赖与实际搜索已有直接反馈，不只依赖 macOS结果。

## 交付材料与边界

实际私有制品为 `runs/iteration13/tools-implementation-20261001/pi-braid-i13-tools-private.zip`，通过下面入口生成：

```sh
python3 scripts/package_agent.py --variant pi-braid-i13 \
  --runtime runs/iteration13/tools-implementation-20261001/linux-runtime-frozen \
  --skills harness/skills --tool-env .env.i13-tools \
  --stage runs/iteration13/tools-implementation-20261001/stage \
  --output runs/iteration13/tools-implementation-20261001/pi-braid-i13-tools-private.zip
```

ZIP大小为393200949字节，SHA256为 `042befe1936840fe353663c88c59f09b69afdd92478da303818f455a686f957d`；清单登记24202个载荷。实际凭据输入、stage配置与 ZIP文件权限均为0600，stage私有目录为0700，ZIP凭据条目为0600。包内 `tool_environment()`实际读取两个非空变量，来源均为包内配置；凭据值不进入记录。具体元数据在 `delivery-materials.json` 与 `packaged-tool-environment.json`。

在 Linux x86_64/CPython3.12容器中解包该 ZIP，使用真实 requirements调用包内 `main.py --prepare-only`，已通过既有包载荷校验并生成最终请求与原生材料。证据入口为 `linux-package-prepare.log`、`linux-packaged-prepared/.factory26/20260930-173218-0a2351e6`（容器使用 UTC）。此前误用 macOS执行包入口被既有平台边界拒绝，原错误在 `packaged-prepare-only.log`，没有绕过平台校验。

最终 runtime身份登记完整 npm/patch hash；npm lock SHA256为 `9b7aa8110d9b2b2befeab075b0c11019a02445d900091e41044dad427d352e4a`。Braid复制源码 SHA256为 `05fdbe32af667dbafc36d40cef80be60e529345784fd5d22f7e08dbb726ca7b5`。runtime记录的 Braid revision是复制时的 Git提交；实际包含工作区修改，以复制源码 hash辨别材料，不能用该 revision或工具提交单独声称可重现所有起点修改。工具提交保留了起点已有的 Pi CLI/生命周期补丁差分、其它任务源码和文档；限定暂存源与 diff归 `tools-stage-source/`、`tools-staged.diff`。

源码与材料范围已经完成，Exa成功检索仍待用户修正 `.env.i13-tools` 中的有效凭据。没有把两次官方鉴权失败改写为成功，也没有重试或替换个人 key。十二处材料装载及真实 SDK session_start不等于所有 Braid Issue/PR最终模型上下文均已验证；未执行 before_agent_start模型调用链或完整生成会话。未运行 Factory/Braid/SVC测试、smoke、probe、模拟任务或模型实验。I12冻结材料与运行未改动，未push。
