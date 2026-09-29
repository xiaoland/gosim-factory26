# I11 当前现场的冷接续准备

本次停止并完整保留 I11 最新现场，准备冷接续包；不操作两个暂停 I10 容器，不操作 pi-minimal。新版 Braid 的 offline-resume 修复由 i11_readable_cli 提供。主线后续已明确授权：完成来源/新 binary/不刷新全体指令的包核对后直接接续，单 GitHub、自有 API、4 GiB/2 CPU；由 i11_readable_cli 核对根 Issue 新会话及模型响应，失败保留新错误、不循环重启。

## 停止身份与状态

来源 run：`pi-braid-i11--hackathon--github-65b879cdc68a1f`。WSL 运行目录：

`/home/yyh/Development/factory26/runs/iteration11/20260929-feasibility/generation/runs/pi-braid-i11--hackathon--github-65b879cdc68a1f`

已先核对 Docker 挂载：`arcbench-local-d5fc0123e57f`（`86c2df0eb915`）的 `/workspace` 唯一挂到该 run 的 `workspace/official-generation`，然后执行 `docker stop --time 30 arcbench-local-d5fc0123e57f`。未修改运行中数据库。停止后外层 run.json 为 `phase=finished`，experiment-result.json 为 `status=failed`，错误为 `Agent generation did not produce a complete application`。这是为修复接续进行的人工停止记录，不是应用最终评分或完整交付结论。

## 保留与接续边界

冷接续目录为 WSL `/home/yyh/Development/factory26/runs/iteration11/20260929-cold-resume/`。`source/stop-record.json` 保存容器停止状态和来源；外层 run.json、experiment-result.json、generation.resource.json 已复制到 source/。原工作目录完整保留。

完整 `source/i11-template.tar` 从停止后的 template 生成，保留 Git、原生会话、应用未提交文件、SQLite、工作树、历史材料与文件模式/链接；工作区 ZIP 从该归档生成，不再次读取正在变化的运行目录。停止后 braid.sqlite3 存在，WAL 已不存在；不创建或伪造 WAL。`braid-state/physical/01a0eda0-7032-7703-a2ec-b935c71d531f/session.json` 已确认在来源中，必须保留，供新版恢复逻辑识别根 Issue1 的失败原生物化。

容器内运行路径仍为 `/workspace/template/.factory26/20260929-042409-1202e245`，不替换旧绝对路径，不更改原 prompt、Profile、模型或技能。此次只替换修复后的 Linux Braid 与恢复 main.py；不使用 `--refresh-native-materials` 触发另一轮材料变化，也不把 I11 再作为从零成绩。

复用 `20260929-feasibility/base-agent.zip`（独立基包），不将旧恢复包及其 recovery-workspace.zip 再嵌套。打包器使用当前 `scripts/package_completed_recovery.py`，当前 recover_completed.py 已移除全工作区逐文件权限扫描。

## 启动交接

`prepared/launch.py` 已按原 launch 接口准备，只改新 agent.zip、experiment-key 与 generation 目录；复用原 feasibility/source 的 lab/adapter/runner 代码和原 gateway，不重装 runtime。启动命令为：

```sh
python3 /home/yyh/Development/factory26/runs/iteration11/20260929-cold-resume/prepared/launch.py
```

该命令已按后续授权执行。第一次 lab create 因预建了空 generation 目录，在任何 run/容器/模型启动前报 FileExistsError；仅通过 rmdir 删除该空目录后重新创建。入口错误留 prepared/launch-preflight-error.txt，第二次启动输出留 prepared/launch.log。这不是模型运行失败后的重复重启。模型凭据由既有 gateway wrap 注入，不写入交接报告或启动脚本。完整归档、修复二进制与最终包身份在完成后补于下节。

## 冻结状态

冻结包为 `prepared/agent.zip`，SHA-256 `4b54da87d1b7f29b297a0bd23db5a1a72c3ddc43831b2c0e8c99067e1d19131b`。

| 制品 | SHA-256 |
| --- | --- |
| source/i11-template.tar（7,112,048,640 字节） | `7c06a1a5bcca0627818e35046f5d8274a6ce5605a93939f45e4f3ebdcbd5ed1e` |
| prepared/workspace.zip（1,638,316,561 字节） | `e10213443af7b786c38bcaca5edad719faa3bbfa9495778455b3da327909cb50` |
| prepared/base-agent.zip | `6743f2e686fc00d73084f97622c05fa7d908fa993ca36019526cf061ddaa8d8e` |
| build/braid | `5c802c32e452ebe8c0de9182bfa4a5298c7cabcf1097d1dccf95ae6a031f17eb` |
| build/braid-source.tar.gz | `24957f29608de36b00ce59a92a66dfd29503d8e52e18aab75132d7dccfcc9e9a` |

ZIP 含 168,226 个文件、34,466 个目录、13,808 个符号链接。完整清单身份存于 source/archive-identity.json；Braid 构建身份存于 build/build-identity.json；打包来源与制品哈希存于 prepared/package-identity.json。

已直接读取最终包确认：来源为本次 I11 run、`mode=workspace-resume`、`refresh_native_materials=false`，包内 Linux binary 的实际字节哈希与新编译产物一致；当前 main.py 不含逐文件权限扫描。workspace ZIP 保留指定失败 physical/session.json、SQLite、origin.git/HEAD 与原 state 路径。未写 live DB，也未以旧 archive 覆盖最新进度。

接续已创建并进入 `phase=running`：`pi-braid-i11--hackathon--github-f402061b5bc88f`。新目录为 `generation/runs/pi-braid-i11--hackathon--github-f402061b5bc88f`；run.json 的 agent SHA 与上述冻结包一致，命令明确 `--memory 4g --cpus 2`，单 GitHub、自有 gateway。已向 i11_readable_cli 交接该目录，由其依据新运行原始记录确认根 Issue 重新物化、原生会话身份及真实模型响应；当前只确认运行器启动，不把运行态当作语义恢复成功。
