# v15 工程化简化设计

## 目标边界

v15 建立一个只支持当前合同的 Python 工程。简化不是减少验证，而是删除历史成功路径、重复权威和只能被专用工具理解的投影，同时保留输入拒绝、文件事务、进程互斥和安装包黑盒验证。

本设计不更换 PDM、测试框架、类型检查器或构建后端，不引入 pre-commit、coverage、测试报告平台或发布管理框架。

## Ponytail 决策表

| 表面 | 当前成本 | v15 决策 | 最小证据 |
|---|---|---|---|
| 代码实现 | config、Corpus、analysis 和 integration 各自携带历史成功路径 | 删除旧成功路径；当前实现直接成为唯一入口 | 当前行为测试 + 旧输入拒绝测试 |
| 静态检查 | 多个命令、mypy 手工文件清单漏掉新增模块 | 一个 `pdm run check` 聚合入口；Ruff 和 mypy 按目录覆盖；保留可单独运行命令 | 故意制造一个未使用导入、类型错误和非法依赖时各门禁失败 |
| 自动化测试 | 子进程等待可挂起，失败输出被吞，临时现场主动删除 | pytest 使用严格配置；每个进程边界有超时；失败包含命令、返回码和有界输出 | 三个故意失败的诊断回归测试 |
| CI | 测试和 wheel 重复构建，质量门禁分散，但黑盒保证有价值 | 静态检查一次、3.11/3.14 测试、只构建一次 wheel、一次完整分发验收 | CI 与本地调用同名 PDM 脚本 |
| CD | Changie 同时承担版本选择和发布事实，workflow 重复 CI 验收 | Towncrier 只写 changelog；release PR 写静态包版本；合并后构建并验证一次再发布同一 artifact | 发布准备演练 + artifact digest/版本一致性 |
| Corpus release | Changie YAML 同时生成 changelog、Corpus 链和 CLI config descriptor | `corpus/version.json` 是 Corpus 唯一版本权威；v15 建新锚点；指南手写 | Catalog 构建和链接/版本校验 |

## 代码实现 hard cut-off

### 配置与 Corpus

- `svc.json` 只接受 schema 3。删除 schema 2 模型、`config_migration.py`、JSON Patch 依赖、迁移 descriptor 和成功迁移测试。
- schema 1、2 或未知 schema 返回稳定的 `unsupported-config-schema`，不得猜测或改写文件。
- `svc upgrade` 只属于 Corpus adoption；删除 `--target config`、配置 guide、双目标调度和 remaining-target 状态。
- Corpus v15 建立新锚点，不保留 v10–v14 的运行时选择链。pre-v15 baseline 返回 `unsupported-corpus-baseline`；v15 不自动把旧项目标记为已采用。
- `corpus/version.json` 采用能表达“当前版本 + 从 v15 开始的后续链”的新 schema。历史发布事实保留在 `CHANGELOG.md` 和 Git tag，不继续打包为可执行迁移链。
- `corpus/migrations/` 只存 Corpus 语义采用指南。配置 schema、CLI machine output 和安装步骤写入 CLI changelog/User Manual，不进入 Corpus guide。

### Analysis 与 evidence

- v15 唯一组合为 analysis v3 + evidence v4；versionless 请求解析为 v3。
- 删除 `v2-on-v3`、`v3-on-v3` 路由及其 query/read 成功路径。evidence v1–v3 和 analysis v1–v2 只返回稳定拒绝。
- 删除仅服务旧成功路径的模型、adapter 和测试。保留版本字段以及旧版本拒绝测试，因为它们是边界可诊断性，不是兼容实现。
- 当前实现是否去掉 `_v3`/`_v4` 文件后缀，以实际能否减少并行模块和导入复杂度为准；不为“看起来整洁”做纯重命名。

### Integration 与运行中进程

- init/status 只识别当前 managed marker。旧 navigation、ignore block 和 legacy CLI Skill 不再自动迁移或删除。
- 发现旧 managed marker 时明确返回 `unsupported-managed-integration`，保留 Consumer 文件不变并给出人工处理动作。
- `_execution.py` 的旧进程互斥不是成功兼容路径，而是防止两个已安装版本同时写状态的安全边界。v15 保留该拒绝检查；只有证明运行目录完全隔离后才能删除。
- 不机械删除所有带 `v1/v2/v3/legacy` 的名字；协议标识、外部输入识别和安全拒绝仍有当前价值。

## 静态检查设计

保留：PDM、Ruff、mypy、import-linter。移除：Changie、zizmor。Towncrier 加入 Python quality/release 依赖组。

Ruff 属于 Python 专用工具，虽由 Rust 实现但不属于待移除范围。import-linter 的六个合同直接保护 analysis provider 中立、计划事务和 CLI 输出边界，保留；如果实现 hard cut-off 后某合同没有真实模块消费者，再逐条删除，而不是整体换工具。

PDM 脚本收敛为：

```text
format          ruff format
format-check    ruff format --check
lint            ruff check
typecheck       mypy
lint-imports    lint-imports
test            pytest
check-generated 当前 output schema、Catalog 和 Corpus version 校验
check           依次运行以上所有只读门禁
```

- Ruff 覆盖 `svc_cli/src`、`svc_cli/tests`、`tools` 和 `tests`，不再只 lint 测试。
- mypy 以 `svc_cli/src/svc_cli`、`svc_cli/pdm_build.py` 和仍存在的 Python tools 为范围，替代易漏项的逐文件清单；第三方无类型信息只做最窄模块级处理。
- `check` 不自动格式化、不生成文件，避免 CI 与本地改变工作树。生成命令继续独立存在，只在作者明确调用时写文件。
- CLI output schema 保留最小的 Git+JSON 版本门禁：输出结构相对上一发布发生变化时，`x-svc-result-schema-version` 必须递增。删除的是 Changie fragment/PyYAML 耦合，不是这个当前消费者保证。
- 不加 pre-commit；CI 和 `pdm run check` 已是同一合同，额外钩子没有独立消费者。

## 自动化测试与可诊断性

pytest 默认配置增加 `--strict-config --strict-markers -ra`，不默认开启 `--showlocals`，避免凭据或大型 payload 泄漏。不全局 `-q`，让失败节点和断言差异保持可见。

针对已观察问题：

1. `test_run_process.py` 的阻塞 `stderr.readline()` 改为带期限的就绪握手；所有 `wait()`、`communicate()` 和 `subprocess.run()` 都有有限 timeout，超时后终止并回收子进程。
2. 子进程断言必须报告 argv、returncode、有限长度 stdout/stderr。复用一个现有测试支持位置中的小 helper；不建立 runner class 或报告框架。
3. `accept_agent_thread.py` 不再把异常统一压成 `error: case`。报告失败 stage、异常类型和有界输出；失败时保留临时目录并打印路径，成功才清理。
4. double cleanup 不再用无信息的 `except Exception` 静默降级；清理失败附带原始异常，但仍尽力终止 carrier，防止泄漏进程。
5. 进程/文件系统测试优先使用 pytest `tmp_path`，让 pytest 保留近期失败现场；纯内存测试不做机械迁移。

新增的最小诊断回归只有三类：子进程非零返回能看到 stderr、启动握手超时不会挂死、分发验收失败会报告 stage 并保留现场。其余改动扩展既有行为边界测试，不复制实现测试。

删除测试的准则是它只证明已删除的旧成功路径；旧输入拒绝、数据不被改写、安全互斥仍保留一个代表性测试。

## CI 设计

```text
check (Python 3.11)
  lock --check -> install locked all groups -> pdm run check
  -> build wheel once -> distribution acceptance once

python-next (Python 3.14)
  install locked runtime/test extras -> pytest
```

distribution acceptance 使用同一 Python 入口，覆盖：

- base wheel 离线安装及依赖边界；
- `svc --help`、output schema 和 Corpus lookup；
- 新项目 `init --apply` 后 `status` healthy；
- 当前 evidence export/query/read 代表路径；
- 未安装 double extra 时明确 unavailable；
- 安装 double extra 后 validate/start/emit/observe/stop 生命周期。

不再为 double 单独重建两次 wheel。Python 3.14 运行源码测试证明解释器支持，Python 3.11 的同一 wheel 黑盒验收证明分发完整性。若未来出现平台相关 wheel，再扩展矩阵；当前 `py3-none-any` 不需要。

移除 zizmor 后不自制 workflow linter。Actions 使用固定 commit，权限最小化；YAML 是否可执行由 GitHub Actions 本身验证。workflow 的业务行为由调用与本地相同的脚本保证。

## CD 与 release PR

保留当前“release PR 合并后发布”的交互：

1. 功能 PR 添加 `.changes/<identity>.<type>.md`；Towncrier fragment 只拥有用户可见 changelog 文本。
2. maintainer 在 release PR 中选择 Behavioral SemVer，更新 `svc_cli/pyproject.toml` 的静态 `project.version`，运行 Towncrier build，提交版本与 `CHANGELOG.md`，并消费 fragments。
3. CI 校验 release PR：版本严格递增、changelog 顶部版本匹配、无待发布 fragments、Corpus 版本变化与 Corpus 源变化一致。任一 CLI output result schema 相对上一发布递增时，package version 必须 major 递增。
4. 合并到 `main` 后，`CHANGELOG.md` 路径触发 Publish workflow。它从 `pyproject.toml` 读取唯一包版本，拒绝已被其它提交占用的 tag。
5. workflow 构建一次，运行与 CI 相同的 distribution acceptance，上传该 artifact；随后依次创建不可变 tag、Trusted Publishing 到 PyPI、用对应 changelog section 创建 GitHub Release。

包版本首次迁移时使用最近稳定 Git tag 的版本作为静态基线；v15 release PR 再显式推进到 `15.0.0`。之后发布判定只比较上一稳定 tag 中的 `svc_cli/pyproject.toml`、当前静态版本与 changelog，不从 SCM 推导构建版本。Corpus 版本继续由 `corpus/version.json` 独立拥有，两者允许不同步。无需复制 core-py 的多产品 release manager；一个短 Python 校验/准备脚本只负责版本、Towncrier 和 changelog 的原子一致性。

CD 不假设 CI artifact 可跨 workflow 复用，因为合并提交与 PR 提交身份可能不同；CD 自己构建一次并发布同一份已验收 artifact。它不再在多个 job 重复构建。

## 工具与依赖处置

| 工具/依赖 | 处置 | 原因 |
|---|---|---|
| Changie | 删除，Towncrier 替代 | 外置 Go 安装且混合 release/Corpus/config 权威 |
| zizmor | 删除，不替代 | 通用 workflow 扫描不是 Python 项目合同；固定 Action SHA 与最小权限已覆盖核心风险 |
| PyYAML | 从根测试依赖删除 | 仅被 Changie YAML 投影/兼容检查消费；double 的 YAML 继续由其 ruamel extra 拥有 |
| jsonpatch | 删除 | 只服务被切断的 config v2→v3 转换 |
| Ruff | 保留 | Python lint/format 的最小统一入口 |
| mypy + Pydantic plugin | 保留并扩大覆盖 | 当前 Python 类型边界已有价值，换工具无直接收益 |
| import-linter | 保留 | 现有合同保护真实模块边界，stdlib/Ruff 不能等价替代 |
| pytest + pytest-asyncio | 保留 | 当前测试与异步合同直接使用；不增 timeout/coverage 插件 |
| semantic-version | 运行时保留 | Catalog/Corpus 使用严格 SemVer；不手写解析器 |
| PDM/PDM backend | 保留 | 已同时拥有 workspace、锁文件、脚本和 wheel 构建 |

## 验证与完成判据

按以下顺序实施，任一层失败不进入发布层：

1. 当前合同：配置 schema 3、Corpus v15、analysis v3/evidence v4 和当前 integration 全部通过。
2. hard cut-off：每类旧输入各一个明确拒绝测试，且文件、进程和 baseline 不被修改。
3. 诊断性：三个故意失败场景输出足以定位命令、阶段和原始错误，且无挂起进程。
4. 静态检查：Ruff format/lint、mypy 全目录、import-linter、生成投影检查全部通过。
   机器输出门禁另用两个失败案例验证：结构变化但 result schema 未递增，以及 result schema 递增但 package 仅 patch/minor 递增。
5. 测试：Python 3.11 与 3.14 全量 pytest 通过。
6. 分发：唯一 wheel 完成 base、analysis、double 和项目生命周期验收。
7. 发布：在不上传的 dry-run 中完成 release PR 准备、版本绑定、artifact 构建与 release notes 提取。

不以删除行数、测试数或 CI job 数作为验收；以权威减少、旧成功路径消失、失败可定位和发布产物只构建一次作为验收。
## CLI 模块边界复查

advisor 的 shift-left 调查结论为 `NEEDS_ARCHITECTURE_CHANGE`。`cli.py` 同时拥有
所有命令语法、分派、领域调用、机器投影和文本/流式呈现，是跨领域 monolith；
`upgrade.py` 与 `integration.py` 当前职责内聚，不因文件体量机械拆分。

拆分以命令所有权为边界：命令模块同时拥有参数注册、执行和呈现，根 CLI 只保留
组合、全局错误交付和退出策略。analysis 与 telemetry 先形成完整纵向切片；double、
dev、run 与 project 命令依同一规则迁移。禁止只创建总 `parser.py` 或总
`renderers.py`，也不引入插件注册框架、handler 基类或依赖注入容器。

后续边界按证据推进：double compiler 仅先抽出路径 containment、bounded read 与
snapshot cache 的资源所有者；provider 分离本地 source discovery/capture 与纯
trajectory normalization，但不统一 Codex delegation 与 Pi history inheritance。
