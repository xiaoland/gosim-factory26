# pi-minimal

直接调用原生 Pi 完成比赛需求。主模型 GLM-5.3-flash（含视觉），唯一子角色为 Kimi-k2.7-code advisor。使用 pi-subagents 与 pi-background-bash；无 SVC、Braid 或阶段调度。

main.py 接受官方 requirements 目录与 --output-dir；从 Runner 环境取得模型连接，原生会话留在输出的 .arc/pi-minimal。build.py 显式选择领域技能、Ponytail lite 与纯Pi预打包环境。配置与正式参赛授权见 tasks/pi-minimal。

```sh
python3 variants/pi-minimal/build.py --runtime runs/pi-minimal/20260929/runtime --output runs/pi-minimal/20260929/agent.zip
```
