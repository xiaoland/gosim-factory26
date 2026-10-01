# Console 生命周期实施回执

2026-10-01。用户明确授权“你可以开始委派收敛braid console了”；本轮完成源码、长期说明和新制品中的真实归档只读反馈，不属于I13，不启动或迁移旧WSL/I12。源码限定提交身份另保存在本轮原始回执的 `commit.json`，无push。

## 实际变更

`service.py` 将程序、构建后的前端、稳定Python身份、受管理binary、接入配置、HTTP身份、轮转日志和人工journal归入独立服务目录。常规prepare拒绝实验临时目录、运行内Python或覆盖已有目标；显式development-output仅供本次新材料核对。server使用冻结程序及登记解释器，同目录锁串行化HTTP与管理操作。配置支持显式binary准备、register、Console自有访问容器start/stop及release；操作保留journal，禁止运行ID重指向，释放后的ID保留墓碑。它不安装到既有服务，不自动创建或移除容器，不停止生成或其它用户进程。

现场继续沿配套CLI和原路径空间。固定Docker context只接受本宿主Unix socket；完整ID、service/run所有权标签及实际最长匹配挂载分别核对，保证CLI binary和数据库来源与GC保护的宿主路径一致。宿主binary冻结到服务目录；旧Docker接线不再强制检查未执行的宿主来源binary，仍属于需显式protect的兼容入口。

`archives.py` 用保存SQLite的只读immutable连接展示对象与讨论关系，不调用可写CLI或原Git，不创建WAL/SHM；非空WAL明确拒绝，不合并或修复。会话目录读取保存的sessions/status，冲突不合并；manifest唯一匹配provider/group/session、工作项及原路径，再核对归档native相对路径、SHA和header。归档POST统一拒绝。缺失或未知材料保留元数据和具体错误，不回退原workspace/容器，不声称完整历史。页面明确保存状态、能力缺口与历史会话；未保存turn字段不冒充零次执行。

`lab/gc.py` 从稳定服务manifest直接派生服务、Python、现场workspace/state/binary/宿主挂载及归档引用；不另维护第二份引用清单。HTTP停止后仍有恢复配置，引用继续保护。解除接入需要HTTP停止、操作方确认无转发、Console自有访问容器已确认停止；缺失容器/未知daemon不能当成功解除。HTTP访问及异常日志每份5MiB、3份备份；人工journal独立追加、flush/fsync，不自动淘汰。本轮仍只有只读GC plan，不改变storage执行政策。

独立advisor先判定归档不能运行当前可写CLI，再核对真实schema映射与收尾边界；最终指出ID复用与嵌套挂载两项风险，已用墓碑和实际最长挂载核对收口。没有新增平台、provider实现或设施测试。

## 前序源码归属与限定提交

起点Factory HEAD为 `db272ce5bb6319159d33430925e1cccdf5c278b4`。Console控制、会话导航、原生读取、讨论根动作和部分样式已有未提交改动；原始28文件快照、完整status、hash及dirty diff保存在本轮 `starting-state.json`、`starting.diff` 与 `before/`。本轮生命周期增量另存 `lifecycle-owned.diff`，便于区分新实现与前序事实。

当前HEAD缺少前序docker_runtime/native_sessions/Sessions/navigation等必要模块，单独提交生命周期局部delta会产生不可运行制品。因此本轮有意收纳完整Console源码及原有任务历史，保留既有读写权限、操作回执、不自动重试、草稿/路由和会话能力；前序实现与历史验证仍按其原任务证据理解。其它仓库dirty不收纳，TDD仅提交本批Console合同段落，起点assignee段落继续留在工作区；sources/braid、I13、provider任务均不修改。

## 实际反馈及边界

Python六文件编译与实际service/server CLI帮助通过，TypeScript及Vite build通过。前端保留既有大bundle警告，没有引入依赖或做构建优化。当前源码与新冻结制品的每份Python源文件身份一致。

新制品使用已有稳定Python3.12宿主安装，位于本次新输出目录 `service-final/`，scope为development-output；它不是长期部署或历史迁移。真实只读实例读取两份已保留材料：

| 材料 | 实际结果 |
| --- | --- |
| `runs/20260920-233128-6aae4ce3` | 1个OPEN Issue、1条Pi会话可读。归档manifest定位原文，首页24条、后续页GET200；浏览器实际显示native ID、工具call/result与文件字节位置。旧schema缺成员、父子及讨论范围的提示可见。 |
| GitHub final extracted evidence | 9个CLOSED Issue、14个MERGED PR、215条会话可读；根Issue87条评论、PR #2的4条评论及展开接口通过。缺native manifest的正文GET400，保留具体唯一映射错误和元数据，没有回退旧现场。 |

Chrome新临时页面实际显示归档只读、23个对象、保存关系与历史provider；根agent有46条provider，其中45条历史。会话直链重载、浏览器back/forward保持身份，缺manifest页面保留明确错误。Pi原文及工具参数/结果已实际加载；没有编辑草稿、提交业务、操作控制或用户原标签。临时页面与本组HTTP实例均已关闭。

两次先期停/复启及最终源码制品的再次恢复均取得/api/runs HTTP200。仅扫描本次服务记录域的GC plan在HTTP运行和停止后均complete=true、零错误、零候选；六条依赖引用完全一致，不把停止当解除。所读归档文件及DB/WAL/SHM的前后SHA全部一致；没有历史GC plan、apply或真实清理。

本轮没有实际验证Docker访问容器启停、所有权/嵌套挂载拒绝、新现场业务修改及pause/resume、register/release管理操作、Codex或其它provider原文、HTTP日志达到上限后的实际轮转。这些分别只有实现与编译证据，不借旧历史验证声称已运行。未验证人工草稿取消/离开保护；保留前序已明确的边界。

## 证据与部署前提

长期操作归[Console README](../../braid-console/README.md)与[部署页](../../docs/deployment/console.md)，跨组件合同归[技术说明](../../docs/product-tdd/index.md)。本轮原始回执在 `runs/braid-console-control/20261001-lifecycle-implementation/`：prepare/build/help logs、service-final manifest/active、http-operations-final、browser-observation、archive-files前后身份、gc-running/stopped-final、restore-final和validation-final。

旧Debian仍不启动，I12暂停现场及既有容器/挂载不操作。真正部署需要在目标宿主选稳定服务目录与解释器、取得可用配套binary，分别确认真实archive或live workspace身份；Docker现场还需实际本宿主context、挂载与新Console自有访问容器标签。旧四ID在Windows当前daemon查不到的事实不能被转换为其它daemon或历史文件已删除；旧接入在实际迁移前继续显式protect。没有需要本轮再授权才能完成的源码工作。
