# pi-minimal-vv Hackathon GitHub / Stage2 正式提交核验

2026-10-08 本任务按用户授权，从当前 `variants/pi-minimal-vv` 工作树和最新本地 Linux runtime 重新装配正式参赛包，目标为 `hackathon--github` 与 `hackathon--github-stage-2`，费用模式固定为 `official_evaluation`。

包身份见 `runs/pi-minimal/competition-20261008-formal-vv/package-identity.json`：ZIP 为 `180571670` 字节、`31166` 成员、全成员 CRC 通过，SHA256 为 `4c0e55f08d24d786c349ebbbdc6fbb12bbff1165d3155b110ca262994a6b7b06`。生产输入是当前工作树 `variants/pi-minimal-vv`、`runs/pi-minimal/evolution-20261006/local-mechanical-20261008/final-runtime` 和已锁定的 E2E addon；本次普通 Hackathon 包未绑定 Evolution 专属 task-context。

创建前通过官方 Client 只读确认：`hackathon` 的 API 状态为 `ended`；`hackathon--github`、`hackathon--github-stage-2` 均返回 `unlocked=true`，Stage2 的 `source_run_id` 为 `4eab9465931a`。原始读回保存在 `runs/pi-minimal/competition-20261008-formal-vv/pre-submit-readback.json`。

随后仅发出一次正常 `POST /submissions`，字段包含 `competition_id=hackathon`、`credential_mode=official_evaluation`、平台注入模型 `glm-5.3-flash`，包上传路径和身份绑定见 `submission-upload-receipt.json`。服务端明确返回 HTTP 400：`This competition is no longer accepting submissions`。该请求未返回 submission ID，因此没有创建或启动任何目标 run；没有改用 `self_funded`，也没有删除或修改已有 submission/run。

本次结果是正式参赛入口的服务端门控阻断，不能据此取得新的 Hackathon 基线。旧参赛/evolution 记录保持原样。

## 已上传提交的 Stage2 启动尝试

随后按用户授权刷新历史并选取最新已上传 submission `aea08b61772c`（不是本次未上传的新 ZIP）。创建前 Stage2 仍为 `unlocked=true`，来源为 Stage1 run `4eab9465931a`；该 submission 已有旧 Stage2 run `32db20c04573`，本次尝试不把它当作重放。

正常 `POST /runs` 只发出一次并被接受，得到新 run `989c53d6deb2`，任务为 `hackathon--github-stage-2`。创建回执显示 `billing_mode=official_evaluation`。随后只发出一次正常 `POST /runs/989c53d6deb2/start`，服务端返回 HTTP 409：`This competition is no longer accepting runs`。GET 读回显示该新 run 仍为 `PENDING`、`started_at=null`；官网历史仍只列旧 Stage2 run `32db20c04573`。平台 GET 的 `billing_mode=self_funded` 字段按已知展示缺陷原样保留，不能覆盖创建回执的正式费用模式。

原始证据位于 `runs/pi-minimal/competition-20261008-formal-vv/`：`history-before-stage2-rerun.json`、`stage2-source-after-create.json`、`stage2-create-receipt.json`、`stage2-start-receipt.json`、`stage2-run-after-start-rejection.json` 和 `history-after-stage2-start-rejection.json`。未重新上传、未删除 submission/run、未启动其它题目，也未改用 self-funded 或绕过门控。
