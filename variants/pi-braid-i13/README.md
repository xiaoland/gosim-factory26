# I13 Harness 开发入口

本页保留 I13 独立实现的源码定位及原入口方法；旧冻结包沿自身材料解释。新 I14 不采用下面直接 main 的入口，使用[公共源码装配](../../tooling/scripts/README.md#i14-源码装配)。下方操作还须核对所用 support 与 runtime 仍满足该历史入口；不能据此跳过新服务 context 或宣称取得新恢复能力。

本目录持有 I13 的生成流程和原生材料；I14 与其它 variant 独立维护自己的实现。本文说明工作树的修改关系，旧冻结包按包内材料解释。

| 想改变什么 | 修改位置 | 需要一起理解的消费者 |
| --- | --- | --- |
| 可指派成员的能力描述、主模型或推理档位 | `agents/<id>/profile.json` | Braid 的成员与主会话配置；不要把它当作 explorer/executor 配置。 |
| 根 Issue 的启动成员 | `run.py` 的 `ROOT_PROFILE_ID` | 只选择根工作项的启动成员；后续 Issue/PR 由 Agent 通过 assignee 指派。 |
| 主会话指引 | `agents/<id>/instructions.md` | native_files 将内容传入本次 Braid profile。 |
| 内部 executor 等角色的模型、工具和技能 | `agents/<id>/agents/<role>.md` | Pi 子代理扩展消费；它不是 Braid assignee。 |
| provider 模型描述与原生设置 | `agents/<id>/models.json`、`settings.json` | Pi 消费；运行时替换实际 endpoint，不能用 descriptor 代替 API 能力事实。 |
| 主会话启用的技能与扩展 | `run.py:native_files` 的 launcher 参数 | 主会话关闭默认发现后显式启用；内部角色有自己的技能声明。 |
| 正式包提供哪些材料 | `build.py` 的选择与对应技能源 | 打包包含文件不会自动启用技能；主会话和子代理所选材料必须实际可取得。 |

例如调整 executor 模型，从该成员下的 `agents/executor.md` 开始；需要新增模型描述时再修改同成员的 models.json。
若为 executor 新增技能，同时考虑它的 skills/skillPath 与包中的材料；不因此改动其他 variant 的角色。
原生接口与精确字段以这些文件及所选原生客户端为准，不在文档另维护全套配置副本。

I13内部角色默认使用独立历史（`defaultContext:fresh`），以本次委派和按需读取取得背景；`inheritProjectContext:false`与`inheritSkills:false`关闭自动继承。角色保留自己的技能发现入口，模型按需读取独立文件。所有Agent Skill的SKILL.md及references正文均不得拼入system、profile、role或task prompt，发现信息只含名称、description和路径；这条约定同时适用于主会话与子代理。历史冻结包保留原身份，不能据当前文档推断其输入已改变。

[pi-braid-i13](.)的角色description帮助调用方选择有委派价值的工作，正文说明用途；不声明角色工具白名单。`settings.json`选择默认基础工具，原生扩展提供委派、联络、等待及后台执行能力。`run.py`只替换角色的技能和扩展路径，不追加父profile、运行条件或方法正文；以`PI_SUBAGENT_MAX_DEPTH=3`限制子层深度。完整工具能力不代替委派的目标与修改范围。原生接口介绍工具使用，技能提供按需方法，不在角色中重复维护。

## 工具与技能接线

`tools/mcporter.json` 仅保留 Handsontable Docs，`run.py` 设置 `MCPORTER_CONFIG`。Context7 与 Exa 使用 Pi 原生扩展，默认供主成员、explorer 和 executor 使用，其它内部角色不默认加载。pi-fff 使用 `tools-only`，覆盖主成员和内部角色，并保留原生 find/grep；不启用可选 multi-grep。精确版本归 [npm lock](../../materials/npm/package-lock.json)，不在本页另存版本表。

`build.py` 选择四项 SVC 方法（documentation、task-packet、sub-agents、verification）及本目录需要的工具技能。独立技能来源和分发规则见 [Harness 材料](../../materials/README.md)，是否启用仍由 `run.py:native_files` 和每个角色的 skills/skillPath 决定。

打包可显式传 `--tool-env`，把 Context7/Exa 凭据写入非 Git 制品的 `.private/tool-env.json`。输入按 dotenv 赋值读取，不执行 shell、不读取个人配置；运行环境同名变量覆盖包内值，主/子进程继承同一环境。含此目录的制品按私有材料保存。

## 直接验证源码

以下命令写出真实原生配置、技能目录和 Braid request，不启动 Braid 或调用模型。
`REQUIREMENTS` 指向本次允许的输入目录。I13 校验目录和实际读取错误，不要求 `requirements.yaml` 作为生成硬门槛；ARC 材料解释由独立技能承担，根 Issue 提供输入入口。历史 variant 的输入要求以其入口为准。

```sh
RUNTIME=$(python3 tooling/scripts/runtime.py path)
python3 variants/pi-braid-i13/main.py "$REQUIREMENTS" \
  --output-dir runs/dev-i13 --runtime "$RUNTIME" \
  --braid sources/braid/target/debug/braid \
  --skills-root materials/skills \
  --base-url http://127.0.0.1:9/v1 --prepare-only
```

输出路径为 `runs/dev-i13/.factory26/<id>`。
从 braid-request.json、work/capabilities 下的原生材料开始检查，不再追踪 effective config 的两层转换。
真实运行去掉 `--prepare-only`，使用实际 base URL，并由调用环境注入 `OPENAI_API_KEY` 或 `FACTORY26_API_KEY`。
密钥不放进源码或命令参数；角色模型由各 variant 固定，MODEL 若提供则必须匹配根角色。

真实运行会产生模型费用，按当前任务的实验授权执行。
每次运行创建独立记录，成功从 Braid delivery commit 导出应用；失败保留工作现场和原始日志。
平台部署布局仍见 [运行文档](../../docs/deployment/index.md)。
