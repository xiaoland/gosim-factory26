# 固定题目能力与 preset 的对应

范围：固定开源 revision 1eb018367bedd618d3b9ced406ce07fb423d4956。explorer 完整阅读 Keep、BookStack 的 requirements.md；仅按 YAML 抽查 12306、Ctrip、PrestaShop、StackOverflow。主 Agent 独立核验 Keep 的自动保存/Undo/搜索和 BookStack 的富文本/草稿关联等影响设计的关键段落。未读官方测试或历史失败答案。以下是用户可观察需求，后一列才是实现上的能力推断。

| 能力 | 题目证据（本地行） | 对现有 preset 的含义 |
|---|---|---|
| 状态持久化、关联与撤销 | Keep REQ-2.2/2.3.2：创建自动保存、删除 Undo（`keep/.../requirements.md:36-72`）；BookStack REQ-6.1.2：draft 出现在 dashboard（`:332-368`） | 是完整应用工程能力；app-engineer/ponytail 可支持实现简化，但题目不要求该 skill 或子角色。这是明确需要覆盖的能力；本次阅读不能据此给全部失败风险排序。 |
| 多实体层级与派生视图 | Keep labels/filter（`:172-246`）；BookStack shelf-book-chapter-page、recent/favorite（`:74-75,327-328,413-454`） | 要求数据模型与跨页一致性；按性质选择局部、集成和用户路径的可执行检查。pi-team 的分工是候选方法，题目不支持据此增设 contract-reviewer。 |
| 认证与会话 | BookStack 登录及 Remember Me（`:31-56`）；12306 注册/登录/重置并持久化（`12306/...yaml:45-45,89-89,231-231,366-366`）；Ctrip 双登录方式（`ctrip/...yaml:44-44,81-81`） | 需要可靠表单验证和会话；具体权限只实现题目明确要求的范围。由主 Agent/executor 建立对应行为检查，不能以专门角色的意见代替会话实际生效的证据。 |
| 复杂交互、暂态与错误文案 | Keep snackbar Undo、七日 trash（`:47-83`）；BookStack 创建/删除确认与取消（`:106-185`）；12306 精确校验错误（`12306/...yaml:104-179`） | 需逐需求浏览器验收；浏览器工具/browser-operator 支持取证，但 native reviewer 不是题目要求。 |
| 搜索、筛选、排序与历史 | Keep 建议筛选、关键字高亮（`:308-333`）；12306 搜索/排序/筛选（`12306/...yaml:463-470`）；Ctrip 城市/日期限制、历史复用（`ctrip/...yaml:558-571,817-839`）；PrestaShop 搜索和多维筛选（`prestashop/...yaml:95-95,391-489`） | 是行为与数据一致性能力；无外部服务/MCP 要求。browser 检查可覆盖结果状态，不能替代实现。 |
| 富文本、图像与视觉复刻 | BookStack rich-text、可选封面图（`:230-244`）；Keep 侧栏/卡片参考图与折叠（`:389-414`）；PrestaShop 商品图片/变体（`prestashop/...yaml:503-571`） | 题目给本地参考资产，要求能读取图像、实现布局与交互。frontend-design/Impeccable、浏览器工具与 browser-operator有相关性；仍不能从题目推出必须使用其中任一项。应先验明模型图像输入。 |
| 社区/交易领域规则（抽查） | StackOverflow 提问/回答 Markdown 与投票（`stackoverflow/...yaml:4-4,737-737`）；PrestaShop 购物车/checkout（`prestashop/...yaml:4-4,637-675`） | 说明 Web 抽查包含社区与购物流程；具体权限、价格/库存语义只按对应需求实现，不从产品名补造完整生产功能；当前 Keep/BookStack Lite 已足以暴露状态与视觉风险。 |

结论：requirements 支持“需求优先、浏览器可观察验收、模型须能读本地参考图”的共同基础；不支持从题目直接推导 MCP、Pi 子代理数量、特定模型或 ponytail/Impeccable/diagnosing-bugs。MCP 为空符合当前需求（未见外部系统调用）；原生 explorer/executor/reviewer 只能作为实现与独立检查的可选手段。此前配置偏通用 Web 开发和视觉技能，尚未形成足够明确的需求→能力→配置依据。需要补的是运行时 Agent 从当次 requirement 识别关键性质、选择观察和建立局部反馈的能力；不能预先把 Keep/BookStack 每条需求编成固定 harness 测试或答案，也不要求每条需求生成永久测试。


## 对本批配置的实际修正

- 共同能力首先保证完整读入需求、依赖/状态/初始数据和本地视觉参考；现有文件/图像工具与任务包承担理解和外置记忆，不增加题目专用 MCP。
- browser-operator/executor 需要能操作真实页面、读取相关截图与控制台/网络证据、复现短暂反馈；主会话接收问题相关结论和证据入口。具体工作划分按 SVC 的问题/效果边界，由 LLM 决定。
- 状态转移、持久化、实体关联、登录与搜索需要一般应用工程及 V&V；不因为缺口出现就自动增加 auth/database/domain 子角色或新的 skill。已有 app-engineer 承担完整功能，原生 executor 的反馈可用 API/脚本/浏览器互补。
- frontend-design/Impeccable 只覆盖界面与交互表达；当它们追求风格创新时，给定参考图、文字、行为优先。是否有助通过率仍是实验假设。
- 正式初赛的完整题包尚未核实，本材料只支持固定 Lite 和已抽查 Web 要求。不能凭赛事介绍宣称已经覆盖 GitHub/Spreadsheets 的完整业务能力。

关键可查源文件：[Keep requirements](../../third_party/arc-bench/arc-bench/webapp/keep/requirements/requirements.md)、[BookStack requirements](../../third_party/arc-bench/arc-bench/webapp/bookstack/requirements/requirements.md)、[12306](../../third_party/arc-bench/arc-bench/webapp/12306/requirements/requirements.yaml)、[Ctrip](../../third_party/arc-bench/arc-bench/webapp/ctrip/requirements/requirements.yaml)、[PrestaShop](../../third_party/arc-bench/arc-bench/webapp/prestashop/requirements/requirements.yaml)、[StackOverflow](../../third_party/arc-bench/arc-bench/webapp/stackoverflow/requirements/requirements.yaml)。
