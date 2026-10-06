# pi-minimal-vv-dx-test

直接调用原生 Pi 完成比赛需求。主模型 GLM-5.3-flash（含视觉），唯一子角色为 Kimi-k2.7-code advisor。使用 pi-subagents 与 pi-background-bash；不引入 SVC CLI、Braid 或阶段调度。

主会话与 advisor 显式启用独立的 svc-verification 技能，build.py 从 harness/skills/svc-verification（指向 sources/svc/skills/svc-verification）物化完整入口与 references，不装入其它 SVC 技能。该方法将需求转为可观察判据、选择检查条件、保留可重复执行证据并解释结果；材料提及的设计步骤由原生 Pi 主会话与 advisor 承担。agent-browser 用于探索与快速反馈，最终验收由主会话按应用需求编写可重复自动化测试或脚本。其已有 with-service.py 可记录执行结果并清理所拥有的服务，不预包应用检查源码。主会话关闭默认技能发现，通过 --skill 逐个加载所选技能；advisor 以独立 skills/skillPath 选择材料。

main.py 接受官方 requirements 目录与 --output-dir，默认从 Runner 环境取得模型连接；使用 `build.py --credentials <models.env>` 时，把获授权的 BigModel 主模型连接和 ARC 自带 key 的 advisor 连接写入本次 ZIP 的 `private-models.json`。ARC 凭据默认读取 `~/.config/factory26/llm.env`，可用 `--arc-credentials` 指定；这不是比赛额度。该私有文件仅进入上传制品，不进入源码仓库。Pi 的 HOME 位于 main.py 旁的 pi-home，PI_CODING_AGENT_DIR 为其中的 .pi/agent；pi-home 链接到输出的 .factory26/pi-minimal-vv-dx-test/home，因此原生配置、子会话、后台任务和主会话证据能随工作区保留。主会话为 .factory26/pi-minimal-vv-dx-test/session.jsonl；不要使用官网工作区下载未包含的 .arc 目录保存实验数据。build.py 显式选择领域技能、Ponytail full 与纯 Pi 预打包环境。该目录是 pi-minimal-vv 的独立 DX 验收派生，不改写基 variant 的历史材料。

```sh
python3 variants/pi-minimal-vv-dx-test/build.py --runtime runs/pi-minimal/20260929/runtime --output runs/pi-minimal/20260929/agent.zip
```
