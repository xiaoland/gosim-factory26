# 执行计划

1. 已确认 pi-team-mixed；收录当前源码、Braid/SVC 来源和既有未提交依赖，使用独占准备目录。
2. 在 WSL 复用现有 Docker 构建缓存和官方 Runner，构建当前工具 lock 与 Braid，冻结一个新 ZIP。使用官方 API 与官方 key，不改变配方。
3. 用已有 arc_matrix/local_experiment 两阶段路径运行完整 Lite 两题，workers=2：生成不提供测试，冻结应用后官方评分。保留原始工作区、Braid 状态、原生角色与会话。
4. 报告完整 Lite 分数和可修复设施问题。参照旧 mixed 的 Keep 27/32、BookStack 30/34，仅作为历史基准，不据单次波动宣称某项改动因果。
5. 本地结果复核后，以 official_evaluation 临时 Key 模式将相同 ZIP 提交官网正式 Hackathon，真实生成 GitHub 和 Sheet。competition 客户端已补齐 credential_mode 接线及正式模式不要求自带 secret 的分支；用户确认本次使用 official_evaluation，仍先复核完整 Lite 结果。保留既有 self_funded 恢复语义。
6. 从实际原生调用和平台日志分别确认多模型和外网查询。模型可列举、宿主网络通或子代理自称成功都不足以证明官网能力；未自然发生的调用保留证据缺口，再决定是否需要额外观察。

已有官网脚本可能需要适应正式任务 id/最新提交字段，先读当前 API；若需要实质改变 Harness 的运行契约或模型，先呈现问题与影响。
监控由既有程序等待终态，远端轮询间隔至少三分钟；不以心跳、token 或源码更新时间代替进展。
不增加次数、token 或耗时预算来抢先终止正常工作，沿用平台与实际模型边界。

## 本轮独立判断与实施影响

实验设计和判别依据见 [design.md](design.md)，不以模型列表、宿主网络或自验次数作为能力结论。
已将 credential_mode 纳入 prepare identity 和 snapshot multipart；official_evaluation 不读取个人 key，self_funded 保持原行为，旧 journal 缺字段按其当时自带 key 语义解释。
官网回传的实际模式须与请求一致；这一条件在提交响应/运行记录核实，不为它创建 Factory 测试。
正式前需从官网 run 取回既有 Braid 原生记录或 OTLP；若平台没有提供这些证据，先标明能取回的范围，不在实验结束后把评分包装成过程分析。

本阶段已按用户授权将其他 variants 标记归档，完成契约调查与两种凭据模式的源码接线；独占 WSL 制品构建及打包已完成，未运行模型或官网上传。


## 当前构建恢复点

2026-09-25 独占目录：本机与 WSL 均为 `runs/hackathon-team-baseline/20260925`，WSL 仓库根为 `/home/yyh/Development/factory26`。
`build-input.tar.gz` 冻结当前 mixed、所需支持脚本、npm lock、已物化 skills 以及 Braid Git bundle/工作区补丁；`build-input/build-input.json` 记录逐文件身份。
`build-status.json` 与 `build.log` 记录恢复源码、Linux runtime 构建和打包步骤；目标为 `runtime-pi-braid` 与 `pi-team-mixed.zip`。
原 Runner/浏览器安装及其他会话的 runtime 不覆盖；Docker 可复用自己的构建缓存。
此步骤不启动模型，不向官网提交；构建成功后才将具体制品和实验材料交给开跑复核。

官网模型表单固定为本 packet 的 model-config.json：GLM 根模型、DeepSeek 视觉模型；DeepSeek 执行与 Kimi specialist 仍由 frozen variant 的原生角色配置选择。
正式 prepare 显式使用 `--credential-mode official_evaluation`，无需个人 key；本地 Lite 另使用已有官方 API key 的私有 env 文件，两者不混用。
首次 WSL 构建在拉取元数据前因缺少 docker-credential-desktop.exe 退出。已为本次公共镜像构建指定独占 DOCKER_CONFIG（空 auths），继续使用现有 daemon/cache，不修改全局 Docker 配置；原错误保留在 build.log，后续输出在 build-retry.log。


构建完成：pi-team-mixed.zip，433,974,971 bytes，SHA256 `7011edab62c1f15f62c002b5bd155eec200880cee893a5e79d0ab65eb418fe3a`。
本机 `runs/hackathon-team-baseline/20260925/ready.json` 保存远端具体启动命令、镜像身份和制品路径；lite-matrix.json 为两题、workers=2、官方 API、两阶段独立生成/评分。
本次构建只完成安装、编译和打包，不宣称运行上下文、API、外网查询或评分已通过。
开跑后完成一个 variant 的完整 Lite（两题 66 项），报告低分及反馈循环分析，再由用户决定官网正式阶段；不扩展其它 variants。
