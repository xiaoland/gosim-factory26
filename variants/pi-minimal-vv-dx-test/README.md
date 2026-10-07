# pi-minimal-vv-dx-test

直接调用原生 Pi 完成比赛需求。主模型 GLM-5.3-flash（含视觉），唯一子角色为 Kimi-k2.7-code advisor。使用 pi-subagents 与 pi-background-bash；不引入 SVC CLI、Braid 或阶段调度。

主会话与 advisor 显式启用独立的 svc-verification 技能，build.py 从 harness/skills/svc-verification（指向 sources/svc/skills/svc-verification）物化完整入口与 references，不装入其它 SVC 技能。该方法将需求转为可观察判据、选择检查条件、保留可重复执行证据并解释结果；材料提及的设计步骤由原生 Pi 主会话与 advisor 承担。agent-browser 用于探索与快速反馈，最终验收由主会话按应用需求编写可重复自动化测试或脚本。其已有 with-service.py 可记录执行结果并清理所拥有的服务，不预包应用检查源码。主会话关闭默认技能发现，通过 --skill 逐个加载所选技能；advisor 以独立 skills/skillPath 选择材料。

main.py 接受官方 requirements 目录与 --output-dir，仅从环境取得 OPENAI_BASE_URL 和 OPENAI_API_KEY。自费供应商链由本目录的 model-recipe.json 声明，公共装配和 model-proxy 负责消费；官网比赛没有 proxy，也不读取供应商配方。此入口不发现 ARC 或其它供应商凭据。

Pi 的 HOME、配置、子会话及后台任务位于输出的 `.factory26/data/harness/<native_scope_id>/home`，主会话为同一 scope 的 `session.jsonl`；Pi 的链接 home 同样在该 scope 内。同任务 restart 使用保留的身份与会话，下一任务创建新的原生状态。observe.py 采集原生事实，status.py 判断活动。build.py 的 variant-only 模式准备程序、角色、技能和原生辅助文件，最终安装材料、服务、输入及提交 ZIP 由公共装配持有。该目录是 pi-minimal-vv 的独立 DX 验收派生，不改写基 variant 的历史材料。

```sh
python3 -m lab start pi-minimal-vv-dx-test sfp7 github-stage-1
```
