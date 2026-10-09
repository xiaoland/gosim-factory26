# 最新 pi-minimal-vv 双题正式提交

本次由侧线独立负责装配、上传与两题启动，不接管主线分析或其它运行。用户明确授权：“没事，我就要"盲目"全量上传‘最新’并且同时启动 github, sheet 两题（而且对刚刚完成的 pi-minimal 分析、改进也已经落地了）。”

范围为当前完整 pi-minimal-vv 源码、技能及当前原生 runtime 补丁；主模型 GLM-5.3-Flash、advisor Kimi K2.7 Code，平台直连，不带 model-proxy、Chromium 或预生成应用。题目是 hackathon-evolution--github 和 hackathon-evolution--sheet；上传 credential_mode=official_evaluation，真实 Agent 生成，消耗比赛额度。沿用 bench/task-context.md 独立文件与入口绑定，官方 requirements 由平台提供。

原正式提交 e2f81e564251 和两题旧评分保留。新保存提交会影响 latest，有 run 即可能替换旧有效提交；用户已明确选择最新全量重跑。只上传一次，不确定写请求先对账，不删除旧 submission。

构建初次失败于 pi-background-bash CLI hunk7，精确日志在下列目录。只在本次 build-inputs/npm 补齐该 hunk 的尾部上下文，保持新增实现不变、共享源码不修改；随后 Docker 正常构建成功，正在导出 runtime。fd 沿用此前已核验 Linux musl 字节。当前下一步为完整装配、字节身份核对及官网同 submission 两题 create/start。完成以两题启动回执和新鲜状态读回为准，尚不声明模型已有效推进或取得成绩。

全部原始记录：runs/pi-minimal/evolution-20261006/formal-latest-20261007/。


## 实际启动回执

2026-10-07 22:59 左右，新 submission `09e2e91cb753` 已正常保存，credential_mode 为 official_evaluation。两题都创建并 start 成功：evo-github `20411b4353c2`、evo-sheet `72c1b6754977`，首次读回均为 STARTING、failure_reason null。start/get 展示 self_funded 是既有平台缺陷，保留真实字段并结合创建 official_evaluation 解释为比赛费用；没有重发启动。旧 submission 未删除或修改。

新包 `pi-minimal-vv-latest.zip` 142223205 bytes，SHA256 `0d5ebe9a3bfed718033597bb3ad67c955779ea40d4a67e4f4320774c1a0a2fc4`，23351 成员。manifest 全部文件哈希已核；vv main/instructions/models/agents/extensions/vendor/tools 与当前源码一致；bench 与svc-verification/check-design、interpreting-results 当前正文一致。PBB、subagents实际装配字节通过 TypeScript strip 与JS syntax编译；没有设施测试或包 smoke。第一编译命令的 Node26 transform 模式不再支持，改用 strip 后通过，记录该区别而非宣称独立运行验证。

构建还暴露 arc-core 剔除重复 ast-grep npm 二进制后遗留失效 .bin 快捷链接；只在独立runtime删失效链接，canonical runtime/bin/ast-grep保留。overlay和补丁上下文修正保留原件。源码总体未改，当前改进通过全新装配实际进入新包；不影响旧正式包及在途其它运行。

完整上传/create/start和新鲜读回见上述运行目录 platform-journal.json、submission-receipt.json、github-*/sheet-* 回执、history-before/after.json。本次请求的装配上传和两题启动已完成，后续生成与评分尚未完成；不自动建立额外监控或接管主线owner。

Helium 原官网 History 读回确认新提交位于首项，两题均 running，旧正式提交仍显示38/60与49.65并标明较新快照已替代。未点选榜或删除。最终新鲜运行状态原件见 *-status-final-readback.json。


## 首次有效生成与费用估算

用户追加要求检查是否真实启动并预估消耗。两题平台预检、安装已完成，状态RUNNING，官方账单/token字段仍null。Helium文件树辨认本次独立native：GitHub a6ccec8ca33e44adb220fda5828a3147；Sheet 1b9ab115c64545d8a95c87c244a71ca7，仅定向读取对应identity/session/stderr/events，排除旧基线证据。GitHub当前可读快照有10assistant完成响应/12工具结果全部成功，最近消息23:02:53；Sheet有10响应/15工具结果全部成功，最近完成消息23:01:39，events尾部仍有连续message_update，显示后续请求正在流式输出。两份stderr为空，没有已记录assistant error/aborted。已证明实际模型和工具执行；未证明全程无后续问题。

采用今天18:27核验过的ARC价格版本（lab/arc_bench/arc-prices.json），本次重新打开Helium Meter仅见密钥登录页，没有读取余额或声称重新核价。Flash输入0.8、输出2.8、缓存0.23 CNY/百万tokens；Kimi输入6.5、输出27、缓存1.3。只汇总本轮root完成assistant消息，GitHub约0.10229264 CNY，Sheet约0.08601096 CNY，合计0.18830360 CNY；进行中的请求、未观察子会话、平台快照延迟不包括在内，不是实时总额或结算账单。原始usage及公式见 startup-cost-estimate.json。

整轮粗估45–60 CNY，参照上一轮同配方双题实际51.310694 CNY；已识别旧GitHub81次尾部推理6.78840336 CNY，若批次通知在同等轨迹避免该部分则双题约44.52229 CNY，但改进验收、调用数和上下文增长可能增加费用，尚无新终态支持净节省。该估计不是费用停止阈值。


## 用户追加 Pi 目录统计脚本

用户原话：“可以考虑写一个脚本，输入 pi 的会话目录就可以统计出 token 用量数据（包括子会话等）”。新增 scripts/pi_usage.py 与 scripts/README.md 对应操作说明；主线源码及现有解析器不改、不提交 Git，不使用子 Agent。脚本复用 native_profile 的字段及时间解析与 arc_spend 的定价算式，只读递归原生session文件；按消息ID/原时间/provider/model去重镜像与fork继承消息，只累计已保存assistant message，保留读取错误、未知字段覆盖数、按session/model及总量。--since过滤继承历史，--prices显式选择价表，--json提供完整统计；不查询API、不发模型请求、不控制在途运行。

真实验证采用此前正式GitHub的已下载project.zip，仅抽取该次native run根内原生JSONL至 usage-validation/old-github：两个会话、674Flash+13Kimi响应，totalTokens169305628，金额41.34183628，与原分析及官方账单41.341827吻合。JSON原件 old-github-usage.json，语法编译通过；没有新增或运行设施测试、模拟数据、包smoke或自检。改脚本与README不会热更新已经上传的参赛包。
