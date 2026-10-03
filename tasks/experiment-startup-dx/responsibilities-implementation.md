# 显式请求与职责分离实施

本轮实施采用 responsibilities-design.md，经用户“开始。”授权。改动位于 feat/experiment-startup-dx 的独立 WorkSSD 工作区，保留主区并行工作和既有运行。

新 experiment schema 3 使用 explicit-request-v1。Build 必须选择 job，仅生产其依赖闭包；start 必须给出 job/request-id，一个请求最多绑定一个 attempt。评价明确选择来源 attempt/output 或 reference/member，不自动消费最新产物。Retry 直接请求一次新执行；容量不足返回阻塞，不登记未来待派发任务。旧 schema 只读及已有 attempt 控制继续委派原冻结执行器。

Controller 与 runner 冻结不同代码闭包，SDK 使用薄入口及只读材料位置，Hosted 保持独立完整交付包。编译只做元数据计划，内容生产和实际引用冻结归选定 job 的 build。公共定义、私有输入及可写状态独立失效；四 I14 variant 使用公共入口和执行上下文。

Hosted 身份/停止核对与重工作区采集分离；单 attempt observer 不拥有派发权限。执行容量在确知物理终态及 writer-close 后释放，归档失败保留自己的责任。入口结果缺失仍保存 unknown，容量释放独立显示；显式 retry 重新核对实时物理终态、准确出生身份、已释放容量及无未决控制，不等待归档。恢复默认只准备，execute 显式创建一个派生 attempt，continue/query/abort 使用同一事务身份；abort 保留当前状态和修复记录，不自动恢复旧 writer。Console attach 登记消费者，query 只读。

成员运输保留原 reference/manifest，只公布完整的所选 member 位置。消费统一解析实际位置，部分成员不能冒充整资产。GC 删除意图冻结成员位置；接收先在 store 锁内核对可用状态，避免删除期间插入未登记字节。原 manifest、member 字节及目录在公布位置前持久化。Advisor 对未知派发效果、GC、接收顺序及恢复 abort 作定点复核，采用缺口已关闭。

## 已取得的实际反馈

原件位于 worktree 的 runs/experiment-startup-dx/explicit-requests-implementation/。

- 用现有 example-intent.json 和真实保存环境完成离线编译：约 0.50 秒，输出 schema 3；无 runtime 安装、cache 生产、Docker、网络或模型操作。独立报告中旧实现同例约 20.33 秒；两次条件和操作职责已变化，此数字只能说明元数据编译成本下降。
- 一次只读查询独立验收报告列出的 12 个真实 I14 目录：文本约 0.37 秒，JSON 约 0.15 秒。资源等待的 memory_current、memory_max、admission 与 PSI 等字段完整渲染；文本以目录为基准区分消费摘要与原生证据入口。运行原件持续更新，不能按旧报告的 active 样本推导当前状态。
- 从既有冻结 executor-code 制品接收真实 lab/exp/core.py：4477 字节，原引用和成员 SHA 一致；接收 store 没有 whole payload。该反馈仅证明这次实际成员路径，不能外推大型资产传输耗时。执行 owner 另保存真实部署文档成员接收回执。

独立验收报告指出的缺少 harness-manifest.json 的 add_note 回归已恢复，多目录查询无需建立额外持久状态库。完整打包、实际首次入口/模型受理、同域热恢复及三类端到端耗时仍未验收；本轮源码、编译及材料反馈不能代替这些结论。没有编写或运行设施测试，也没有接管源实验。
