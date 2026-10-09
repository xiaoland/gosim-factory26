# WSL 空间清理

状态：完成。五个大停止容器的关键数据已核对并补存到 Mac WorkSSD，随后按精确 ID 删除；WSL 可用空间由约 13 GiB 增至约 48 GiB。

## 目标与授权

用户要求处理 WSL 空间占满问题，并于 2026-10-07 明确同意：确认停止容器的关键数据已保存在 Mac mini 的 Factory26 工作区后，可以删除这些容器。

关键数据包括运行输出与应用、Git/Braid/native 状态、运行日志和退出事实。可重新构建的 Harness ZIP、runtime、依赖缓存和重复恢复包不作为保留条件。当前运行中的容器和仍被运行使用的卷不在删除范围。

## 当前事实

- WSL `/dev/sdd` 已从无可用空间恢复到约 13 GiB 可用；未重启 Docker。
- 已删除导致本次故障的 9 个 core 文件，并清理 BuildKit、无用镜像及系统缓存。
- WSL 已生效并持久化 `kernel.core_pattern=|/bin/false`；Lab 新容器入口已增加 `--ulimit core=0:0`，源码改动尚未提交。
- 待核对的五个大停止容器合计约 36 GiB；其主要占用来自重复 Harness ZIP、runtime 和恢复工作区包。

## 完成判据

逐个容器确认 Mac 回收目录包含对应 `/job/output` 的关键内容，保存容器 inspect、diff、控制脚本、stdout/stderr/exit 等补充证据；随后按精确容器 ID 删除并核对 Docker 与文件系统空间。任何没有对应回收件或内容不一致的容器保持不动。

## 结果

删除前确认五个目标均为 `exited`。主要续跑结果的关键内容与既有 Mac 回收目录一致；旧 Web 的变化 Git index、旧 GitHub 的九项恢复记录差量，以及各容器的控制脚本、stdout/stderr/exit、精简 inspect 和 diff 已补存到 `runs/wsl-space-cleanup-20261007/container-preservation/`，并生成、验证 `SHA256SUMS`。可重建的 Harness ZIP、runtime、依赖缓存和重复恢复包未重复传回。

已删除容器：`51a4c6d2fa94`、`d953d25b48d6`、`0f17383d713b`、`5d81e5470ee8`、`d1972d275199`。未删除卷，两个原有运行中容器保持运行。删除后 `/dev/sdd` 为 125 GiB、已用 77 GiB、可用 48 GiB、占用 62%。
