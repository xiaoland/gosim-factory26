# 第二轮剩余工作

用户已经授权落实三项，不需要再次复核原有方案。

## 实施顺序

1. 让历史查询、官网客户端脱离旧生成器，删除无当前消费者的配置式生成和评测入口。
2. 在现有 inspect_runs / factory show / feedback / viewer 中识别 local_experiment 目录，连起原始生成、部署、评分、应用和会话路径。
   不根据退出码猜分数，不把缺少证据当作零分，保留原始错误文件。
3. 提供开发 SVC 的显式源码安装入口，以及独立 Git 工作树的 bundle + 工作区补丁交接。
4. 更新现行文档，通过已有真实记录查询、生成页面和实际源码归档/恢复操作取得反馈。

无 Factory/设施/Corpus 测试，也不创建替代它们的自检；不启动模型实验，不改远端 journal。
实施前工作副本保存在 runs/developer-experience/remaining-before。
源码恢复面向新目录，不覆盖既有工作树；Git index 的暂存划分不跨机器保留，修改内容、未跟踪文件和本地提交保留。

## 已核实事实

.venv 中开发 SVC 为 sustainable-vibe-coding 15.0.0，安装元数据仍指向 sources/svc/cli（当前参赛树已裁减 CLI）。
完整开发源码在相邻 ~/Development/svc；安装必须明确选它，不能再依赖参赛树的旧路径。
现行官网脚本从 factory.py 导入凭据/JSON 写入，导致历史执行器仍在运行依赖中。
旧 submission/main.py 只通向已拒绝运行的 shared-config 入口；concurrency.py 只调旧评测器。

## 实施结果

- `factory.py` 只保留 list/show/analyze；删除配置式生成/评测、SSH 评测、bootstrap、batch 分支，以及无消费者的 concurrency 和 shared submission。
  官网工具改用独立文件操作与平台凭据入口，core 只保留仍由 variant 使用的会话归档，删除无人调用的 Codex 旧 transport。
- `inspect_runs` 识别嵌套 local_experiment，show/status/feedback/viewer 接通实际生成、部署、评分、应用、原生会话和原始日志。
  JSON 保留完整错误；HTML 用可滚动区域呈现错误并链接原文件；默认文字摘要只列核心证据。
  部署依据官方 runner-events 的应用可达事件及之前的失败，不以容器退出码推断得分。
- `runtime.py dev-svc --svc-source` 显式安装完整开发源码，记录路径、HEAD、dirty 状态及 CLI 版本。
  `sources.py export/restore` 交接 bundle、binary diff、未跟踪文件和 shallow 边界，恢复到新目录。
- 修正 raw OTLP InstrumentationScope 缺失一层 protobuf message 的编码；没有重写旧批次，也没有启动模型链路验证。

## 实际操作与证据

1. 已读取真实 raw Pi / DeepSeek / Keep 先导记录：生成 completed、部署 completed、评分 completed、27/32。
   评分容器退出 1，仍保留其完整评分，外层适配器退出 0。
   摘要和反馈位于 `runs/developer-experience/existing-local-evidence.json`、`existing-local-feedback.json`。
2. 相邻 `factory26-official-local/runs/viewer/index.html` 已生成 108 条既有实验的页面；本仓 viewer 生成 30 条，均无发现阶段警告。
   这些数目是归档记录数量，包括历史准备/失败记录，不是新增实验或新增 bench 成绩。
3. 开发 CLI 已从 `/Volumes/WorkSSD/Development/svc` 安装为 15.0.0；来源记录 `.bootstrap/dev-svc.json`。
   此操作不升级或修改源码 Corpus。
4. 三个真实工作树均已 export 并恢复到新位置。
   Braid 与开发 SVC 归档位于 `runs/developer-experience/recovery/`，恢复在 `restored/braid` 和 `restored/dev-svc`。
   参赛 SVC 的第一次恢复暴露浅克隆边界缺失；修复为同时携带 Git shallow 信息后，归档在 `recovery-v2/factory-svc`，恢复在 `restored/factory-svc-v2`。
   原源码树没有 fetch、reset、提交或修改；未跨机器安装/重建，不据此宣称 WSL 环境已恢复。

Git 忽略文件和 index 的暂存划分不交接；各仓库恢复分开执行，不宣称跨仓库原子快照。
源码归档和实际恢复是本次交付操作，不新增 fixture、mock、自检或测试套件。
