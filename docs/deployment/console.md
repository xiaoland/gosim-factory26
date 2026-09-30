# I12 实时协作 Console

此页面供开发者在获授权的 I12 实验中查看并人工介入 Braid Issue/PR。它直接读取当次 Braid state，写入操作只调用该次配套的 `braid --state PATH --external`，因此沿用 Braid 的对象事务、事件和消息投递。页面与服务不进入参赛包。评论作者显示为 `external`；CLI 投递回执只证明接收状态，不证明 Agent 已消费。

在运行所在的 WSL 主机创建独立 registry JSON，明确列出已批准的运行及其配套 Linux binary。`state` 指包含 `braid.sqlite3` 的目录；I11 对照可登记为只读。路径不要指向归档副本或其它实验。

```json
[
  {"id":"i12-github","label":"I12 GitHub","kind":"i12","writable":true,"state":"/absolute/run/github/braid-state","binary":"/absolute/run/github/bin/braid"},
  {"id":"i12-sheet","label":"I12 Sheet","kind":"i12","writable":true,"state":"/absolute/run/sheet/braid-state","binary":"/absolute/run/sheet/bin/braid"}
]
```

上例路径是字段格式，不能直接运行；以当次 packet 冻结的实际路径替换。服务启动时检查路径和执行权限，不支持动态添加或从目录自动发现运行。以运行目录内的 journal 保存人工介入输入和 CLI 实际输出，避免与 Braid 原始证据混放：

I12 本轮两个运行的登记保存在 `runs/iteration12/recovery/console-runs.json`（Git 忽略的运行材料）；WSL 恢复完成后先确认登记中的 state 与 binary 均存在，再将该文件传到 WSL 同一运行目录使用。

本轮在 WSL 仓库根目录实际使用的参数为 `--registry runs/iteration12/recovery/console-runs.json --journal runs/iteration12/recovery/console-actions.jsonl --port 8765`。服务 PID、日志分别在同目录的 `console-server.pid`、`console-server.log`；Mac tunnel PID 与日志在 `console-tunnel.pid`、`console-tunnel.log`。停止时先按 PID 核实进程命令，再终止对应服务或 tunnel。

```sh
python3 lab/console/server.py --registry /absolute/path/i12-console-runs.json \
  --journal /absolute/path/i12-console-actions.jsonl --port 8765
```

服务只监听 WSL `127.0.0.1`。Mac 浏览器通过 SSH 本地端口转发访问；从 Mac 执行 `ssh -N -L 8765:127.0.0.1:8765 <WSL-host>`，然后打开 `http://127.0.0.1:8765/`。不要把服务绑定公网接口或转发给其他用户。registry 的运行标签会明确区分 I12 可写与 I11 只读。

列表和当前对象每五秒刷新；编辑中的标题、正文或评论草稿不会被轮询覆盖。对象视图保留可见讨论；隐藏评论和已解决的历史默认折叠，点击展开时才调用 `comment view --include-hidden`，展开的线程在后续轮询中更新。正文优先使用已有的 `markdown_it` 渲染，原始 HTML 与自动图片加载被禁用；缺少该库时安全地显示原文。列表、详情与按需展开都使用配套 CLI 的 JSON 读接口。编辑采用完整正文替换，提交前以对象 revision 检查已观察到的并发变化。Braid CLI 没有原子 revision 前提，提交瞬间仍可能发生并发编辑；关键正文变更应在刷新后确认。评论、回复、隐藏原因、解决线程、关闭与重新打开均为一次明确 POST，不自动重试。若 CLI 超时、进程错误或回执不确定，页面显示原始错误并要求先刷新状态和检查 journal。

journal 每次写入前持久化 `started`，CLI 返回后追加 `completed` 与原始 stdout；未确认结果追加 `unconfirmed` 与实际错误。保留原始输入，包括人工输入的正文，因此 journal 只放在受控运行目录，不对外发布。它是独立的介入记录，不代替 Braid 数据库与原生过程证据。页面仅展示当前保存的正文、讨论和关联，不推断未观察到的 Agent 阅读或 Git 改动。
