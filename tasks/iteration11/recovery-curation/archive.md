# I10 原始成果归档与 I11 可编辑副本

状态：已完成（只读复制与归档）。原始 workspace、Git、SQLite/WAL、native 会话和证据均保留；未启动模型、未解除容器暂停、未修改原件、未运行测试或探针、未提交。

## 来源与运行状态

两份来源都位于 WSL 主机 `wsl.win-ws.localhost`，归档前确认对应容器仍为 Docker `Paused`：

- GitHub：`/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs/pi-braid--hackathon--github-7fe42a1248f9d8/workspace/official-generation/template`
  - 容器：`f26-continue-db0f28e3288046`（`Up 6 hours (Paused)`）
  - `.factory26` run：`20260929-042409-1202e245`
- Sheet：`/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs/pi-braid--hackathon--sheet-3b5e3eeaa3b062/workspace/official-generation/template`
  - 容器：`f26-continue-a2ce3ac2d41459`（`Up 3 hours (Paused)`）
  - `.factory26` run：`20260929-042409-811f18d4`

两份 `run.json` 均保留在副本中，记录 `variant=pi-braid`、`backend=pi`、`workflow=braid`、`svc=true`、`status=generating`、`phase=braid`，且 `generation_finished_at=null`。这表示归档的是暂停时的完整现场，不能把它解释为已完成或失败的运行。

## 完整原始归档

归档目录：`/Volumes/WorkSSD/Development/factory26/runs/recovery-curation/original-archives/`

采用未压缩 POSIX tar 流从 WSL 读取整个 `template` 目录，保留目录结构、权限、符号链接及隐藏目录；不是 Git-only 或 SQLite-only 快照。

| 来源 | 归档文件 | 字节数 | SHA-256 | 条目数 |
| --- | --- | ---: | --- | ---: |
| GitHub | `github-template-20260929-042409-1202e245.tar` | 4,023,705,600 | `dfa6525456a22c58f699838833dba553b189af4016cf26a1d3e8bc6937e59baf` | 214,642 |
| Sheet | `sheet-template-20260929-042409-811f18d4.tar` | 4,493,660,160 | `aab7d5d7956b849f64b20179b7922e314164a4b1bbf9577b6ebab8d189cfdaae` | 139,461 |

每个 tar 均包含顶层 `template/`，以及 `.git`、`.factory26`、SQLite 主库与 `-wal`、native 会话、证据和未提交文件。归档是只读来源的完整字节副本；没有删除或裁剪数据库，也没有输出凭据内容。

## 独立可编辑副本

副本目录：`/Volumes/WorkSSD/Development/factory26/runs/recovery-curation/editable/`

- GitHub：`editable/github/template`，`du -sh` 约 `3.4G`；166,801 个普通文件、13,804 个符号链接。
- Sheet：`editable/sheet/template`，`du -sh` 约 `4.0G`；103,117 个普通文件、8,910 个符号链接。

副本由对应完整 tar 展开得到，符号链接和模式保留；为使 Mac 副本可直接编辑，展开时使用了 `--no-same-owner`，因此本地所有者是当前用户，归档中的权限信息仍保留。两份副本均已确认存在对应 `run.json`、`braid.sqlite3`、`braid.sqlite3-wal`、`native` 和 `.git`。

容量检查：WSL `/` 约余 73 GiB，Mac `/Volumes/WorkSSD` 约余 464 GiB；当前归档和副本均落在 Mac `runs/recovery-curation` 下。

## 恢复限制与后续使用

- 原始路径仍由 WSL 暂停容器持有；本次没有解除暂停或把现场推进到新状态。需要恢复时，应先在副本上核对，再由有权限的负责人决定是否恢复原始容器。
- `status=generating`、`phase=braid` 且没有 `generation_finished_at`，所以不能从这份归档宣称 I10 终态、评分、部署或新一轮运行已经完成。
- tar 保留了 Git、工作树未提交内容、native 会话、证据、SQLite/WAL 和运行元数据，但跨主机恢复仍可能需要重新映射用户/路径/容器环境；副本所有者已改为本地用户，原始容器身份和运行时不会随归档自动重建。
- GitHub 与 Sheet 的整理负责人应只在相应 `editable/*/template` 副本上工作；原始 workspace、归档 tar 和其中的证据不应被裁剪或覆盖。GitHub/Sheet 外部平台材料另有负责人，本归档不代替其整理。
- 本次没有执行 I11、评分、模型调用、部署或测试，也没有修改原始成果。
