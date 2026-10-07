# I14-dx-test Braid 基线导航

这是 I14 共同基线的独立 DX 验收派生。Cleaner、Reviewer、E2E 是各自独立的实现目录，不是这个目录的运行开关。需要改变本实现的生成流程、角色接线或交付记录时，先看同一目录的 `run.py`；技能与原生支持材料由 `build.py` 准备。本实现通过 `--prepare-only` 只写原生材料和 Braid 请求，不调用模型。

## 按问题定位

| 问题 | 先看 | 反馈/边界 |
| --- | --- | --- |
| 改本实现的生成流程、workspace、交付或归档 | [`run.py`](run.py) 的 `generate()`、`native_files()`、`copy_application()`/`deliver()` 调用 | 结果和错误写入本次 `--output-dir`；不要把 [`build.py`](build.py) 当运行控制器 |
| 改本实现的根成员/内部角色材料 | [`agents/`](agents/) 下的 `profile.json`、`instructions.md` 和 [`run.py`](run.py) 的 `native_files()` | 角色由原生材料生成；模型绑定由运行时 route 冻结，不能只改 prompt 推断通道变化 |
| 改本实现的技能和工具载荷 | [`materials.json`](materials.json) 的技能声明、同目录 [`extensions/`](extensions/)、[`tools/mcporter.json`](tools/mcporter.json) | 只影响冻结包材料；扩展须在 `run.py:native_files()` 中显式装配 |
| 改供应商模型配方 | `model-recipe.json`；角色模型仍归原生 profile 和 agents | 公共 proxy 消费自费供应商链，原生适配只使用 OPENAI_BASE_URL/API_KEY；比赛不应用供应商配方 |
| 改应用检查反馈 | `run.py` 的应用检查、delivery 与归档段落；应用结果写入 run evidence | 反馈来自实际运行、交付和归档回执；不把外部评测实现复制进变体 |

Lab 调用 `build.py --variant-only` 准备程序、角色、技能和原生支持；公共装配加入容器内安装器、公共服务与输入，统一入口再调用 `main.py`。原生状态保存在 `.factory26/data/harness/<native_scope_id>`，同任务 restart 保留会话，下一任务使用新原生状态。observe.py 采集事实，status.py 判断活动。Braid 扩展和提交历史发布时机仍在 `run.py` 中维护；I14 不沿用 I13 README 或材料选择推断行为。

## 共同扩展边界

共同运行扩展是 `pi-subagents`、后台 Bash、observer、`pi-fff`、Context7 和 Exa；`factory-pi-timing.ts` 是变体目录中的额外原生扩展材料。它们在 `native_files()` 中被装配并写入本次运行的 capabilities；`extensions/` 本身不是独立的生成入口。技能由 `materials.json` 声明，公共 producer 保留组件，运行时建立小型链接树，包内存在不等于当前会话启用。

源码核对：[`main.py`](main.py)、[`run.py`](run.py)、[`build.py`](build.py)、[`extensions/`](extensions/)、[`tools/mcporter.json`](tools/mcporter.json)。
