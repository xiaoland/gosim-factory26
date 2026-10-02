# continuation-03 token profile

> 已由[终态 token 复审](token-final-review.md)接续：09:20 是统计起点；终态修正了无头原生续写漏计、子代理与恢复副本口径。下文保留为历史截面。

统计 cutoff：2026-09-28T09:20:00.180875Z。按原生 JSONL 每条记录的 `timestamp`/`at` 过滤，usage 仅在包含 `usage.input` 的单个 message 记录计数一次，避免递归重复累计同一 usage 对象。

|题目|模型|有效请求数|input|output（含 reasoning）|cacheRead|cacheWrite|
|---|---|---:|---:|---:|---:|---:|
|GH|glm-5.3-flash|370|616,847|108,090|29,216,960|0|
|GH|deepseek-v4-flash|59|75,456|30,009|2,551,168|0|
|Sheet|deepseek-v4-flash|2,015|2,347,336|999,547|266,225,280|0|
|Sheet|glm-5.3-flash|614|1,603,360|183,004|55,024,192|0|

来源：attempt-09 复用 workspace 下 `.factory26/**/work/home/.pi/pbb/sessions/**/instances/**/events.jsonl`；GH 完成归档后 native-homes 中存在同一 session 记录副本，按 `(file.name, record.id, timestamp)` 去重后得到上表，故 GH 初始 2 倍数值已修正。标准 continuation-03 run 目录只含控制器 telemetry。未做费用估算（无单价）。
