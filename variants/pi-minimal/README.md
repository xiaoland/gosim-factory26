# pi-minimal

直接调用原生 Pi 完成比赛需求。主模型 GLM-5.3-flash（含视觉），唯一子角色为 Kimi-k2.7-code advisor。使用 pi-subagents 与 pi-background-bash；无 SVC、Braid 或阶段调度。

main.py 接受官方 requirements 目录与 --output-dir，默认从 Runner 环境取得模型连接；使用 `build.py --credentials <models.env>` 时，把获授权的 BigModel/Moonshot 连接写入本次 ZIP 的 `private-models.json`，主会话和 advisor 分别直连两家供应商。该私有文件仅进入上传制品，不进入源码仓库。Pi 的 HOME 位于 main.py 旁的 pi-home，PI_CODING_AGENT_DIR 为其中的 .pi/agent；pi-home 链接到输出的 .factory26/pi-minimal/home，因此原生配置、子会话、后台任务和主会话证据能随工作区保留。主会话为 .factory26/pi-minimal/session.jsonl；不要使用官网工作区下载未包含的 .arc 目录保存实验数据。build.py 显式选择领域技能、Ponytail full 与纯 Pi 预打包环境。配置与正式参赛授权见 tasks/pi-minimal。

```sh
python3 variants/pi-minimal/build.py --runtime runs/pi-minimal/20260929/runtime --output runs/pi-minimal/20260929/agent.zip
```
