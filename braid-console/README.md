# Braid Console

独立的 Braid 协作界面，和 Braid CLI 一起使用，不依赖 SVC 或 ARC。它保留在 Factory26 父仓库中，没有独立 Git 仓库，也不进入参赛包。

`web/` 使用 React、TypeScript、Vite、Ant Design 和 TanStack Query；负责对象浏览、Markdown讨论、草稿及操作回执。
`server.py` 提供 HTTP 接口并服务构建后的前端，所有对象读取与修改调用登记的 Braid CLI；不直接写数据库或另建调度逻辑。

先在 `web/` 执行 `pnpm install --frozen-lockfile` 与 `pnpm build`，再运行：

```sh
python3 braid-console/server.py --registry /absolute/path/console-runs.json \
  --journal /absolute/path/console-actions.jsonl --port 8765
```

registry 明确列出真实 Braid state 及其配套 binary；读取和写入均使用该身份。权限来自 `writable`，不由迭代名称推断。

```json
[
  {
    "id": "github-current",
    "label": "GitHub 当前运行",
    "writable": true,
    "state": "/absolute/run/braid-state",
    "binary": "/absolute/bin/braid"
  }
]
```

服务监听 `127.0.0.1`。运行在WSL时，从Mac使用 `ssh -N -L 8765:127.0.0.1:8765 wsl.win-ws.localhost`，打开 `http://127.0.0.1:8765/`。
新增运行或更新路径后，以新registry重启服务；不把旧运行ID重新指向新state，以免旧草稿写到新工作项。

Braid状态里的Git与工作树路径属于生成时的执行环境。运行在容器中时，宿主侧`state`与`binary`保存实际来源身份，另用可选`cli_command`指定同一环境中的CLI基础命令，例如 `docker exec -i <运行容器> env -u BRAID_AGENT_RUNTIME -u BRAID_STATE -u BRAID_CLI_BINDING_ID <容器内braid> --state <容器内state>`，将各参数写为JSON字符串数组。服务只在该命令后追加既有对象操作，不改变数据库里的路径，也不在失败后偷偷换到其它副本。registry由宿主维护，浏览器不能提交执行命令。

读接口使用原生Issue/PR及comment JSON；写接口通过 `--external` 执行编辑、评论、回复、隐藏、解决、关闭与重开。
正文编辑保留观察到的revision，发现已改变时要求刷新；CLI没有原子的revision前提，提交瞬间的并发编辑仍需人工核对。
讨论resolve作用于整条thread，局部整理使用hide及原因。隐藏与已解决历史按需展开，后续新回复保留可见性。

每次修改在独立journal保存原始输入和实际CLI回执。CLI写入失败或超时不自动重试；先核对真实对象与journal。
消息入队、负责人读取和业务完成是不同事实，界面不根据CLI成功推断Agent已经采用指示。
当前运行的身份、资源、暂停与实验条件归对应task packet，不写在通用页面协议中。
