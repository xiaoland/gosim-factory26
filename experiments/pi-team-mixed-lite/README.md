# pi-team-mixed 本地 Lite 两阶段矩阵

该配方只生成官方本地 Runner 的机器清单，不启动 Agent 或模型。`pi-team-mixed` 是当前活动 variant；输入使用冻结 ZIP，Keep 与 BookStack 各独立生成后再评测。需要在 WSL 的仓库根运行，Runner、题目、镜像、网关 env、并发与输出由调用方指定。

```sh
experiments/pi-team-mixed-lite/matrix.sh /path/to/pi-team-mixed.zip \
  --inputs-root /path/to/platform-inputs \
  --runner /path/to/runner \
  --image /path/to/image \
  --env-file /path/to/gateway.env \
  --workers 4 \
  --output /path/to/experiments/<id>/manifest.json
```

这一步只解析并核对输入。执行生成的 manifest 用 `python3 -m lab.run run <manifest> --runs-root /path/to/experiments/<id>/runs`。不要把该命令视为已授权的新实验；每次实际运行的输入和完成条件以任务包为准。
