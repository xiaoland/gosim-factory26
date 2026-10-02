# 实验基础设施

新实验只使用 `factory26.exp.experiment` schema 1。Controller 组织构建、派发、控制、监控和分析；Local/Docker 的独立 runner 持有单个 attempt 的入口、资源限额、原始采集和保全。托管 adapter 持有平台身份与 pending 写入。旧 plan/run/operation writer 已从工作树退役，历史材料通过 `history` 或专用只读 reader 消费；不翻译成新执行。

```sh
python3 scripts/runtime.py host-exp --python /absolute/python --purpose controller --output /absolute/controller-runtime
python3 scripts/runtime.py host-exp --python /absolute/python --purpose runner --output /absolute/runner-runtime
python3 -m lab build /absolute/recipe.json --directory /absolute/experiment
python3 -m lab start /absolute/experiment --deployment /absolute/private-deployment.json
python3 -m lab status /absolute/experiment --json
python3 -m lab control /absolute/experiment ATTEMPT stop --request-id REQUEST
python3 -m lab stop-evidence /absolute/experiment ATTEMPT --output /absolute/stop.json
python3 -m lab analyze /absolute/experiment --output /absolute/new-analysis.json
```

配方显式冻结 authorization、controller_runtime、Local runner_runtime、jobs、max_parallel、budget.max_attempts 和 storage.host_reserve_bytes。job 声明 purpose（build/prepare/generate/evaluate）、backend、argv（托管无需 argv）、inputs、outputs 与 wall_seconds/storage_bytes/telemetry_bytes。字符串授权只记录已经取得的许可，不授予执行。`inputs` 接受显式 source，或 artifact_id/manifest_sha256 和可选源 store；独立评价还可消费 `{from_job, output}` 的已发布生成制品。命令中的 `{workspace}`、`{inputs}`、`{attempt_dir}` 和输入名由实际执行环境展开。

公开 environment 冻结模型与供应商政策，私有 deployment 只引用 credential_file/cookie_file。credential_file 为 JSON 环境映射，不能覆盖公开模型、endpoint 或 runtime 政策。`FACTORY26_MODEL_BINDINGS` 以 native provider 或 `native-provider/model-id` 选择通道，分别声明 provider、base_url、credential_env；特定模型可显式声明 model_id 别名。Harness 将按模型覆盖拆为不同原生 provider，并同步 profile 与角色，避免共享 provider 的 key 覆盖其它模型。费用模式由托管 backend 显式声明，不因 endpoint 改变。

Docker endpoint、不可变 image_id、共享 slots 和 daemon 派生 admission_volume 显式冻结。接管还需 authority_handoff：全部旧派发者已停止、旧预留为空、在途窗口关闭的独立原件。`authority-handoff --endpoint JSON --writer OWNER_JSON --registry OLD_REGISTRY --authorization SCOPE --output NEW_JSON` 只读核验已明确列全的退役范围，不停止 owner 或释放槽。paused/alive 不等于退役；现有旧现场不自动迁移。

`control ... export` 仅接续终态保全和输运。`retry ... --authorization SCOPE --request-id REQUEST` 在冻结 attempt 预算内登记明确的新 attempt，再用 `start` 接续 controller。未知效果不授权新入口；重复原 dispatch request 不重跑 main。执行退出、归档、遥测封口、producer flush、输运和评分分别报告。Controller completed 只表示声明执行和证据流程结束，outcome 与平台评分仍独立。

制品用 `artifact import/verify/export/transfer` 发布、核验及装配，`evidence` 按受限 member/字节游标读取。导入历史字节不会取得新执行证明。`telemetry snapshot/batches/export/ingest` 保留 stream/epoch/源序列、原始 protobuf 与错误；摄取同源批次幂等，冲突原件保留。Analyze 固定原件摘要和采集截止点；没有调用身份时模型用量明确未知，不从原始批次数推导 token 或费用。

Harness checkpoint/prepare 的公共生产接口、来源停止门控和路径限制见[恢复说明](../docs/deployment/recovery.md)。模型/收费生命周期与跨环境恢复的尚未取得实测见[任务 packet](../tasks/experiment-dx-review/packet.md)。本仓库不运行设施测试或 smoke；真实离线材料取得的反馈不替代模型实验验收。
