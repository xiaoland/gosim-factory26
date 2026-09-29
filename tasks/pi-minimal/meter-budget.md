# pi-minimal Meter 余额保护

状态：已安装保护脚本；当前正式比赛余额高于门槛，可以启动，但必须持续止损。

## 已核实的账户与当前余额

Meter 页面 `https://meter.arc-bench.com/user` 的现有登录会话显示个人访问密钥账户：

- 接口：`GET https://meter.arc-bench.com/api/user/balance`
- 余额字段：`balance.available_balance`
- 货币字段：`currency`（页面显示 CNY）
- 同步状态接口：`GET https://meter.arc-bench.com/api/user/freshness`
- 当前只读结果：`available_balance=23.001318`、`currency=CNY`、页面账单状态“已同步”、更新时间 `21:41:48`

该账户 `available_balance=23.001318 CNY`，但它是自带 API key 的 Meter 账户，不是 `official_evaluation` 的比赛额度，不能用它决定正式参赛是否可启动。

正式比赛额度来自官网只读接口：

- 接口：`GET https://arc-bench.com/api/competitions/hackathon/registration`
- 关键字段：`competition_type=official`、`registered=true`、`initial_budget_cny=500.0`、`remaining_budget_cny=285.862202`、`currency=CNY`

因此当前正式参赛余额为 **285.862202 CNY**，高于用户授权门槛 100，可以启动。CLI 用保存的网站会话访问该接口，保护脚本对 HTTP/身份/schema 错误 fail-closed，不猜测余额，也不输出 cookie 或 access key。Meter 的个人账户接口仍记录在上面，避免把两种余额混淆。

## 保护路径

[budget_guard.py](budget_guard.py) 只接受并解析为以下唯一 journal：

`runs/pi-minimal/20260929/official`

首次检查：

```sh
python3 tasks/pi-minimal/budget_guard.py runs/pi-minimal/20260929/official --once
```

持续检查：

```sh
python3 tasks/pi-minimal/budget_guard.py runs/pi-minimal/20260929/official
```

脚本启动即查询一次，此后每 600 秒查询。正式比赛余额不高于 100 时写入该 journal 的 `budget-stop.json`，并检查 `state.json` 中的每个 run：先读取状态和 `submission_id`，只对属于该 journal submission 且未终态的 run 调用既有官方取消接口 `POST /api/runs/{run_id}/cancel`，再读取状态确认。余额查询失败也写 `reason=budget_unavailable` 的停止标志，阻止继续启动；不会取消未经身份核对的 run。

`--check` 只查询一次且不取消，适合每次开始下一题前的闸门：

```sh
python3 tasks/pi-minimal/budget_guard.py runs/pi-minimal/20260929/official --check
```

主线 Competition controller 已检查同一 journal 的 `budget-stop.json`，存在该文件时拒绝新的远端写入，因此它会阻止下一题的 snapshot/create/start。脚本不持有 controller lock；余额事件和取消回执仅写 `budget-events.jsonl`，不写凭据。

## 限制

- watcher 使用现有 ArcBench 网站会话查询比赛额度；不能把任何 cookie 或 access key 写入仓库或命令输出。
- 保护是“停止新增远端写入 + 取消同一 submission 的在途 run”；它不取消其他历史 journal，也不删除或改写比赛证据。
- 本次只做了源码语法与真实只读额度核对，未上传、启动、取消任何比赛 run，未调用模型。
