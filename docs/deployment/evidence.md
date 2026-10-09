# 运行证据

## 按记录生产者查询

先确认拿到的是 Lab run、Harness 内层目录还是平台 journal。它们记录不同过程，运行状态和评分不能互相替代。

| 材料 | 查询入口 |
| --- | --- |
| 当前 Lab run | `python3 -m lab status RUN --json`、`python3 -m lab logs RUN`；原件位于 manifest 和 records。 |
| Factory 生成目录 | `python3 -m lab.analysis.factory show --run RUN`；定位 `.factory26/<id>`、交付记录和原生 manifest。 |
| 历史 Factory / ARC 归档 | `python3 -m lab.analysis.run_feedback brief RUN`；只读解释原记录。 |
| Braid 遥测 | [Braid 诊断](braid-diagnostics.md) |
| 官网运行 | 保存的 journal、平台 run ID 和官方结果；记录观察时间，历史文件不证明当前远端状态。 |
| 旧 experiment/attempt | [lab.exp](../../lab/exp/README.md)及其原冻结执行器 |

```sh
python3 -m lab.analysis.factory show --run RUN --case REQ-2.2
python3 -m lab.analysis.factory show --run RUN --json
python3 -m lab wait RUN --json
```

查询消费保存的事实，不新增采集循环。停止等待不会停止执行。原始错误、HTTP 状态与响应内容是诊断依据，token 增长或进程存在不能单独证明任务取得进展。

## 原生会话与分析

Factory 归档的 `native/manifest.json` 关联物理 session、provider、工作项与内容哈希。旧记录没有 manifest 时仍可读取原文，但关联保持未核实；归档缺项不自动改写应用结果。生成之后发生的外部评测错误未必存在于生成 transcript，应先从评测结果定位应用缺口，再定向回看实现过程。

```sh
python3 -m lab.analysis.factory analyze --run RUN
.venv/bin/svc analysis query --help
.venv/bin/svc analysis read --help
```

`analyze` 使用开发侧 SVC，为原生会话导出带 provenance 的 evidence ZIP；安装入口见 [CONTRIBUTING](../../CONTRIBUTING.md)。来源变化需要重新导出，不能用新文件替换旧来源身份。用量与账单分别记录，未完成请求和缺失 usage 保持未知。

需要浏览多个历史归档时可生成静态快照：

```sh
python3 -m lab.analysis.run_viewer --root . --output runs/viewer
```

页面不轮询平台，更新后需要重新生成。相对产物链接依赖本机保留的归档，原生正文、批次和工具输出分享前应检查是否包含私有信息。

## 保存与缺口

当前数据布局、`lab save` 的规范包范围与凭据排除规则由 [Lab](../../lab/README.md)维护。规范包、原始官网下载 ZIP 和完整可恢复环境是不同材料；来源与缺项需随保存回执交接。

冻结 SQLite 的原件不应直接打开：只读连接仍可能产生辅助文件。需要调查时，将数据库及已登记的 WAL/SHM 复制到新的分析目录，读取副本。材料不完整时保留具体缺项，不重写原 manifest。

派生应用目录可能在清理后不存在。沿 archive/artifact manifest 和 ZIP 寻找保留原件，需要提取时写入新的目录并记录来源；分析副本不自动具备完整检查点或继续生成的身份。目录名、completed 状态或未见消费者都不是删除数据的充分理由。
