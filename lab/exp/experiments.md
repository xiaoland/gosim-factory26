# 实验定义与编译

本页对应 compiler.py、readiness.py、environment.py 和 CLI 的 compile/doctor/build 前半段。

实验定义放在 experiments/，运行结果放在 runs/。compile 消费显式 intent，冻结 intent、recipe、compilation receipt 及输入/政策身份；不安装 runtime、不请求平台、不调用模型。targets 必须显式列出 case、variant、model，compiler 不自动展开矩阵或从名称猜授权。selection_policy 和 evaluation_policy 也必须显式声明，评分原件只作为选择依据，不授予执行许可。

environment profile 只解析明确的 runtime、cache、Python、skill/tool 和 OTLP 位置，不能覆盖模型、费用、需求或恢复决策。doctor 只读检查冻结材料、宿主、Docker 和凭据变量，不创建资源、不初始化域、不预约槽位；缺少当前证据时返回 unknown。

build 重新核对编译输入和实际字节，复用或生产缺失资产并发布冻结 compilation evidence。相同输入、政策和 compiler 版本可重入同一 bundle；任一变化须使用新目录。build 成功表示材料冻结，不表示模型启动或入口 ready。

定义快照与运行数据分开。运行目录通过 experiment.json.definition 绑定源路径、消费字节 SHA 和快照 artifact；源文件可变化或消失，但运行只核验冻结快照。历史 recipe 按原 schema 解释，不由新 compiler 翻译。

## 输入合同

实验使用 `factory26.exp.experiment` schema 2，环境使用 `factory26.exp.environment` schema 1。environment 必须声明 `id`、`cache_root`、`python`，并可在 `harness` 下声明 `runtime`、`skill_source`、`tool_env`、`e2e_runtime`、`otlp_dependencies`、`provider_env`、`application_seed`、`gateway_routes`；这些路径和依赖由 profile 冻结，不能借 profile 覆盖模型、费用、需求或恢复决策。生产者还可声明 `definition_assets` 作为恢复检查点的定义依赖；它必须随 repair 显式绑定 artifact/member/store，不能从旧目录推断。

Intent 的必要选择包括 experiment_id、authorization、execution、cases、variants、models、targets、selection_policy 和 evaluation_policy。models.config 只公开 model、visual_model、provider、base_url；native bindings 使用 provider、base_url、credential_env、model_id，公开配方只保存变量名。FACTORY26_MODEL_BINDINGS 支持 native-provider/model-id 覆盖，Harness 按模型拆分原生 provider，避免共享 key 互相覆盖。

targets 是显式列表，compiler 不自动展开笛卡尔积。selection_policy 可为 explicit 或 final-score-margin；后者必须绑定相同 case 集合的真实 run_id、终态、百分数和完整测试数，缺失材料只按显式 on_incomplete 处理。evaluation_policy 可为 none 或 per-application；评价通过 from_job/output 消费已发布生成制品，不能继承生成的收费许可。

recover 的 intent 必须包含 `recovery` 且键集合严格为 `production`、`target`、`repair`；target 与 checkpoint 保持同一 logical run root、OS 和 architecture，并明确目标 runtime identity。替换 runtime 时还须核对 Braid、native hook 与 Pi 协议兼容性，具体定义换版和 store 解析见 [制品合同](artifacts.md)。repair 只接受 v3 producer 支持的 `definition_assets`、`provider_bindings`、`transient_links`、`nodegyp_tools` 修复，不因历史目录缺失而猜测替代物。recover 只生成新的 prepared 输入，不停止来源或启动模型。

doctor 的输出应区分声明、冻结、实际配置和已观察事实；Docker daemon/image/slots/handoff、模型变量覆盖、runtime identity 和 producer 原件均以 observed/blocked/unknown 呈现。它不创建容器、初始化域、释放预约、安装工具或请求官网；start 另行重验这些门控。
