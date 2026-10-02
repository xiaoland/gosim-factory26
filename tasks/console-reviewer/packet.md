# Console reviewer 阅读修复

2026-10-02。独立会话负责 Console 专属接线，不修改共用 Braid、runtime 或 operation，不操作生成、dispatcher 或运行槽。用户授权为：“有明确显示接线缺陷就实现、实际验收并部署到现有唯一Exp Console”，以及本任务 git commit、不 push。

实际 PR2 为 MERGED，pr view 保存 review #1、reviewer-1、completed / approved；status physical 枚举保存 review:1 / pi-glm-reviewer。当前 Console 仅按 issue/pr 过滤并且没有 review 详情入口，导致审阅执行者在 PR 中不可见，不是未派发。

方案复用登记 CLI 的 pr review view、现有 provider 目录、原生分页与 Trace；PR 下新增审阅深链，分别保留 PR、review、agent、provider 身份，显示冻结候选、实际结论作者、checkout 和证据。历史 provider 不受 completed/merged 过滤。旧 binary 没有 review_requests 的 PR 不调用新增 CLI。验收使用编译、真实 PR/session/API 与浏览器操作，不新增基础设施测试。

唯一服务先核对为 8cc80cad-d873-49ed-ab49-e958ba8852a3，PID924012，Debian-Rebuild 稳定根 20261001-i13-2-compatibility-release；七条登记保持。升级保留配置、journal、访问容器与 binary，不注册重复 run 或新 watcher。

证据入口：runs/console-reviewer/{pr2-before,sessions-before,review1-cli}.json。下一步完成接线、真实验收，冻结程序并切换原服务。

## 实施与真实验收

已完成。PR2 的 review #1 实际责任为 reviewer-1 / revision2，冻结候选 f15176b5f386e5571da14fc12517f16bccc7c064，2026-10-02 03:10:07（上海时间）结论为 approved。原始数据库的 review_checkouts 与 conclusion_agent 均为 01a0f8cb-1b1a-7ee2-a36c-80ba54c7d384，provider_sessions.session_id 为 01a0f8cb-6397-7150-9cec-e77244ec46ec；physical 记录为 01a0f8cb-42c8-72d3-bad2-9a33bd6c7e50，native ID 为 01a0f8cb-5419-7011-b7d5-584f9746d14c。provider / assignment 当前 sleeping，review completed 后 execution=null，不代表未派发或记录丢失。证据为 database-links.json、review1-cli.json、review1-http.json、readback.json。

页面新增 PR 下 review 深链及实际结论、候选、checkout、冻结需求、证据入口。review 会话不混入相关 Issue 的全部会话；只有结论/checkout 明确 agent 身份时链接原 Issue 目录。原 provider 目录保留全部已发现记录；历史 replaced/retired 判定和正文分页沿用现有能力。

第一次实际点击发现遗漏的页面身份比较：choose 没有比较 review，因此忽略 PR→review 的导航。补齐后再次构建及部署，真实浏览器依次点击 PR2 审阅入口、reviewer agent、provider，看到输入 Review 1 - pending - @reviewer-1 及候选 f15176b；Trace 显示 read/bash 工具调用、call ID、参数和 toolResult。最终 provider 深链直接刷新仍可读，再通过 breadcrumb 返回审阅结论。原始 UI snapshot / screenshot 为 review-ui.txt / review-ui.jpg。未发送评论、修改对象、暂停/恢复生成或运行测试。

最终唯一服务在 /home/yyh/.local/share/factory26/exp-console/20261002-review-sessions；service ID 保持8cc80cad-d873-49ed-ab49-e958ba8852a3，HTTP PID1676167，instance8ccaaf92-02f0-4a60-904e-5564ba6957c3，上海时间2026-10-02 10:20:38启动。各次切换均先校验新程序与原依赖，核对并停止旧HTTP，保存旧配置/active/launch/journal身份及退役原manifest后启动唯一新HTTP。七条原run配置完全保持，未重复注册、创建访问容器或变更其labels。原binaries/source与归档仍以原绝对路径登记；新manifest继续保护它们。部署证据为 deployment.json / deployment-current.json；旧根及中间根保留历史材料，当前均无manifest权威恢复入口。

TypeScript/Vite构建、Python编译和diff空白检查通过。七条run的Issue与sessions均200、access_error=null，review1正文首页50条/146641字节读取200；错误PR归属调用返回400并保留具体CLI错误。已完成独立advisor的导航归属/历史语义及部署切换判断，验收来自实际数据库、HTTP和界面操作。

边界：当前归档格式的review详情未接入，直接报告缺失而非从评论推断；本次证明MERGED PR现场的已完成review可读，并非宣称离线归档覆盖。IssueOwner结论关联入口无本次真实样本，仅专属reviewer完整链路已实际验收。正文按原reader分批加载，本次取证与页面验收没有宣称读完全部414931字节或独立复核生成应用的Approved质量。没有Braid调度问题证据，也未改调度。

收尾进一步核对深链父对象：review会话目录复用同一review详情查询核实PR归属，错误PR3/review1/provider页面实际返回400具体归属错误并不展示原文；最终正确PR2完整链路、Trace、深链刷新及返回审阅再次通过，证据为wrong-parent-ui.txt、provider-ui.txt、trace-ui.txt。HTTP服务最终身份以deployment-current.json为准，前序制品仅保留切换取证。
