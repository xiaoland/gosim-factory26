# 入口修正后的自购 API Lite 验收

状态：重跑两题均在生成阶段因 GLM API 余额/资源包不足失败，无评分；等待用户恢复供应商额度。
授权：用户明确要求开工，并用其另行提供的 Kimi、DeepSeek、GLM key 重跑完整 Lite。

## 范围和材料

唯一 variant 为 pi-team-mixed，WSL 官方 Runner 对 Keep、BookStack 两题并发运行，生成与隐藏评分分开；完整 66 项结束后报告。
新实验目录为 runs/hackathon-team-baseline/20260925-interface，保留前一冻结包和结果。
复用 WSL 已安装 Runner、runtime 依赖和 Docker 缓存；本轮只重建改变的 Braid 二进制并重新打包入口与技能。
模型角色与原生配置不变，不另设 token/耗时上限，不增加设施或 Corpus 测试，不运行官网。

凭据读取项目 .secrets/models.env；已核对三家 /models HTTP 200，不打印 key。
Kimi 与 GLM 包含 kimi-k3、glm-5.3-flash。
DeepSeek 目录为 deepseek-flash、deepseek-v4-pro；官方文档说明 deepseek-v4-flash 与 deepseek-v4-flash-vision-exp 仍可调用，但实际统一由 V4.1-Flash 承接。
依据：https://api-docs.deepseek.com/zh-cn/ 与 https://api-docs.deepseek.com/guides/vision/。
因此不需要另选视觉供应商，也不能把本轮与旧官方网关的分差归因于入口修改这一单一变量。

## 接入与执行

复用已有 LiteLLM 网关和 Linux Python runtime，在独立端口 4014 启动本轮实例，不影响既有 4010/4012。
网关增加 mixed 所需 deepseek-v4-flash 路由；通过 --preserve-parameters 保留本轮客户端推理/采样/输出参数，已有原生 raw 实验仍默认使用其原有供应商默认模式。
请求元数据分别记录客户端预算、规范化参数与上游参数；不以 /models 成功替代真实多轮工具执行。
只将本网关临时访问 token 及 URL 传给容器内 variant，厂商 key 留在宿主网关环境。
ARC 适配器清除宿主 OPENAI_API_KEY 等变量，避免官方 Runner 用自购 key 请求 Meter；不回退官方地址或凭据。

完整实验期间由程序持有等待，间隔至少三分钟；监控角色为 gpt-5.6-luna/low，只汇报终态或明确阻断。
完成后主 Agent 综合评分与工作过程，证据采集可独立委派，不以调用次数作为协作收益。


## 当前恢复点

WSL 控制器 PID 1065260；execution.json、controller.log 与 controller.pid 位于上述新实验目录。
精确程序为本 packet 的 run-interface-lite.py，其副本与输入源码归档留在实验目录。
新输入包含 Braid bundle/工作区 patch、独立 variant、完整技能、模型网关与 lab 运行代码，97 个文件；不覆盖旧 runtime 或源码。
终态监控为 /root/interface_lite_monitor（gpt-5.6-luna / low），程序三分钟采样，构建/实验结束或控制器失联才返回。
本轮新增网关 preserve 参数分支已作 Python 语法编译；没有运行设施或 Corpus 测试。


## 连接中断

终态监控已启动，但持续 SSH 等待约 263 秒后被远端关闭；没有收到实验终态。
主 Agent 再次独立连接也返回 `kex_exchange_identification: read: Connection reset by peer`（172.16.249.14:122）。
SSH 无 ControlMaster/ProxyJump，因此不是复用陈旧控制连接；新增 ServerAlive 参数的重连仍在握手阶段失败。
最后实际读到 execution.json.phase=packaging，Linux runtime 导出已成功；新 Lite 结果尚未取得。
控制器使用 start_new_session=True 启动，SSH 断线本身不意味着它已停止。恢复后先读取原目录和 PID，不重启整个脚本、不重复生成或重跑已有任务。

终态监控已被要求改为本机程序每 180 秒做一次短 SSH 查询（ConnectTimeout=10），连接失败在程序内等待，恢复后接着读原 execution.json；不重启实验。
用户已收到“是否正在调整 WSL/网络”的补充问题；这是当前缺少的外部状态信息。


## 重启后的接续

2026-09-25 再次连接成功，uptime 18 分钟；旧 PID 1065260 不存在，ZIP 尚不存在，lite-runs 尚不存在。
这次中断发生在打包中，不是已启动的 Lite 失败，也没有已有生成任务需要重跑。
原执行状态保存为 interrupted-execution.json。任务脚本支持显式 --from-packaging，跳过已完成的源码恢复与 Linux 构建。
新控制器 PID 23623，controller-resume.log；原目录、runtime、模型接入与两题矩阵保持相同。
监控已交接新 PID，仍使用本机程序每三分钟短 SSH 查询。


## 模型请求失败与当前阻塞

控制器 23623 已结束。两条生成记录 Keep `865260aadf`、BookStack `dba6560303` 均在约 21 秒内失败，未进入评分，不是有效零分。
原始网关错误为 `litellm.UnsupportedParamsError: openai does not support parameters: [thinking], for model=glm-5.3-flash`。
已将供应商字段 thinking 放入 extra_body，保留上游请求含义；修正已同步 WSL build-input/scripts/hackathon_gateway_compat.py，Python 语法编译通过。
现有 ZIP 不受此网关修正影响；恢复时使用 run-interface-lite.py --from-running，跳过归档提取、构建和打包，以免覆盖修正。

WSL 默认 DNS 172.29.144.1 超时，223.5.5.5 和 1.1.1.1 的直接 DNS 查询正常。再次通过系统解析器查询 open.bigmodel.cn 仍返回 Temporary failure in name resolution。
尝试用 sudo -n 备份并临时修改 DNS 时要求密码，没有修改系统配置。已请用户在 WSL 恢复 DNS，不接收密码。
恢复后保存本次失败执行状态，启动新控制器并记录 PID，继续原实验目录；保留两条失败记录，单独统计后续完整评分。


## DNS 恢复后接续

用户通知恢复后，三家模型域名均解析成功；不携带凭据的 HTTPS 请求均返回 HTTP 401，确认网络及 TLS 到达服务。
确认没有旧控制器或本网关仍运行后，保留 gateway-parameter-failure.json，使用 --from-running 接续。
新控制器 PID 18037，日志 controller-retry.log；复用 433977913 字节的原 ZIP 和已修正的网关，未重新构建或改变模型配方。
已通知原监控 Agent 接管新控制器，继续每 180 秒检查终态；旧两条网关失败记录不纳入得分。


## 本次重跑终态

Keep b4e918eca4 与 BookStack e62eaed80d 均约 163–165 秒后生成失败，未进入评分。
模型请求已到达供应商，gateway/gateway.log 返回 HTTP 429：余额不足或无可用资源包,请充值。模型组 glm-5.3-flash，网关重试两次后仍失败。
控制器 18037 与本网关已退出；不继续重试，不回退官方 key，不更换模型配方。需恢复该 GLM key 的余额/资源包或由用户提供可用接入。
主 Agent 在用户询问进展时读取到终态；监控未及时回传，已要求其停止等待并报告实际状态。
