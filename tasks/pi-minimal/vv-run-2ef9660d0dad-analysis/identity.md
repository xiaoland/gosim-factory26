# 身份、冻结材料与取证边界

2026-09-30，只读核对；本轮未启动生成、模型调用、应用或评测。原始证据根 [E](../../../runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/)，旧证据根 [O](../../../runs/analysis/pi-minimal-github-20260930/20260930T031746Z/c3fea0c3488c/)。下面 `A` 指 E/extracted/template，`M` 指 A/.factory26/pi-minimal/session.jsonl，`V` 指 A/.factory26/pi-minimal/session/fb04a836-51cb-48dc-8940-b29ddf178785/run-0/session.jsonl。行号为原文件的一基行号。

## 官方结果与提交

|字段|旧 run|新 run|
|---|---|---|
|官网 run|[c3fea0c3488c](https://arc-bench.com/runs/c3fea0c3488c)|[2ef9660d0dad](https://arc-bench.com/runs/2ef9660d0dad)|
|submission|f12fdf5540a1|2dbbc244c485|
|任务|hackathon / hackathon--github|相同|
|名称|pi-minimal-glm-arc-advisor-20260930|pi-minimal-verification-github-20260930|
|run详情 score / 通过 / 失败|2 / 2 / 98|4 / 4 / 96|
|功能|0/47|1/47|
|原生生成结果|exit_code=0, terminal=stop, continuations=0|相同|
|官方阶段|生成、安装部署、评测完成|相同；FAILED 是总终态，不能解释成未生成或未启动|
|计费模式|self_funded|self_funded|
|新 run 时间 UTC|—|started 04:42:54.130372；finished 06:22:58.228966|

依据为 [旧 status](../../../runs/analysis/pi-minimal-github-20260930/20260930T031746Z/c3fea0c3488c/status.json)、[新 status](../../../runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/status.json)、各次 journal 的 inputs/state/history，以及本轮只读保存的 `E/submissions-selected.json`。官网新日志记录前端安装和 Vite build 成功、后端安装成功、`mini-github listening on http://0.0.0.0:3000`。不能把日志中的部署成功解释成业务验收成功。

**评分字段须分开：** `/runs` 返回新 score=4.0、test_pass_rate=4.0；最新 `/competitions/hackathon/submissions` 对相同 run 返回 passed_count=4/100、test_pass_rate=4.0，但 task `score=3.538969688863313, score_regime=penalty`。旧对应 task `score=null, score_regime=unavailable`，通过率仍2.0。submission总分还把未运行Sheet纳入两题汇总（新总分1.7694848444316564、test_total=200），不作为本次GitHub分数。报告“2→4”沿用run详情与通过数口径，不能称为综合计费/排名分数增加2分；本轮不猜测penalty计算公式。submissions查询曾返回HTTP 500，后续同一只读查询成功，保留了早期local snapshots与当前响应；没有改controller的旧RUNNING快照。

新 status 的 tests=[]、node_states={}、result_path=null；commit-history 返回 `availability=workspace_unavailable, commits=[]`，traceability 返回同类不可用状态。当前材料不能指认官方哪 4 例通过、哪 96 例因哪个断点失败，也不能确认私有评测跳过了什么。

## 上传包、binary 与 Git

|项目|旧|新|
|---|---|---|
|冻结 ZIP|runs/pi-minimal/20260930/arc-advisor/base-agent.zip|runs/pi-minimal/20260930/verification-github-123247/agent.zip|
|SHA256|b4196fd387909a21a39a34e8c10f2a69c621057c7ed4f0647b60db3eeaf66e6a|4edbd960caf21a51d8a83195761a07ec8df0f06f4d8c62fea7d161dfcf0a3216|
|manifest capabilities.variant|pi-minimal|pi-minimal|
|Pi / subagents / background Bash|0.85.1 / 0.56.0 / 1.0.5|相同|
|manifest 载荷文件数|23,761|23,766|

两包 SHA256 已重新读取 bytes 计算。manifest 对比为 **5 个新增、6 个修改、0 删除、23,755 个文件哈希相同**；Node/Pi runtime、工具依赖、扩展、Ponytail 和其余七项技能的载荷哈希没有变化。两份 manifest 的 npm_sha256 与 native_patch_sha256 也完全相同。本次无 Braid binary；这是纯 Pi variant。

新增只有 svc-verification 的入口和四份 references。修改的实际范围是：

1. `main.py`：显式 skills 增加 svc-verification；增加 `--no-skills` 关闭默认发现，保留逐项 `--skill`。
2. `instructions.md`：加入 V&V 的介绍/读取时机，要求真实 UI 自动化、保留候选/命令/输出/退出码，介绍已有 with-service.py。
3. `agents/advisor.md`：增加技能声明和设计/验收方法说明，职责仍是 fresh 只读咨询。
4. `skills/agent-browser/SKILL.md`：恢复指向 svc-verification 的结果解释提示。
5. `agent_support.py`：恢复执行权限前先检查已有 mode，避免不必要 chmod；不是生成逻辑变更。
6. `runtime-executables.json`：104 个路径的列表顺序改变，集合相同。

完整比较见 `E/package-diff.json`、`frozen-text.diff`、`additional-frozen.diff` 和 `frozen-materials/{old,new}/`。因此不能称为仅改了一个 Skill 文件，也没有证据把低分归为运行了旧 ZIP。新实际 provider 系统目录确实多出该 Skill，实际用户指令确实包含新段落。

新冻结回执记录源码提交 `6cd8d2a`，本地可解析为 `6cd8d2a977bffb196321bc1ce9cd3a5db7e40fa0`；它是开发仓库来源记录，不是生成应用 commit。manifest 未记录可复现整个工作树的 Git tree，SVC 来源还含既存 dirty 修改，故复现应以 ZIP 和逐文件哈希为准。旧包没有取得可单独证明其全部内容的 Git commit。两次下载均不含 `.git`；新主会话没有 `git` 调用。官网 commit-history 又不可用，**生成应用的 Git OID 未取得**，以工作区 ZIP 和逐文件哈希固定交付证据，不编造 commit。

## 模型、完整可见提示与 Skill 版本

两次原生主模型均为 `bigmodel/glm-5.3-flash`、thinking=high；advisor 均为 `arc/kimi-k2.7-code`、thinking=high。官网 model_name 只是 glm-5.3-flash；真实双路由由 identity、原生 model_change/assistant messages 和冻结 private config 的相同哈希互证。地址分别为 BigModel 的 `https://open.bigmodel.cn/api/paas/v4` 与 `https://api.arc-bench.com/v1`。未打印认证值。

|原生会话|旧|新|
|---|---|---|
|main ID|01a0efe4-7d83-7106-aa8f-3ee6679cb85c|01a0f09f-9678-7459-b7e3-a9387e7a4ef5|
|main 行数 / assistant消息|711 / 347|551 / 263|
|advisor ID|01a0efea-1822-77f0-94ca-1fafda39f0ed|01a0f0a3-f2dc-70ff-ae30-15b754195ac9|
|advisor 行数 / assistant消息|52 / 21|55 / 22|

已取回 main/advisor 原生 JSONL、provider-facing capabilities JSON（含 system 和 tool schema）、user-instructions.md、原始 advisor 输入/输出与 meta。完整可见提示入口：

- `E/new-provider-system-glm-5.3-flash.txt`、`new-provider-system-kimi-k2.7-code.txt`，对应原始 capabilities 文件 `8574ee93…json`、`8d584c54…json`。
- 对照 `E/old-provider-system-*.txt` 及 `provider-system-*.diff`。主 system 仅新增 V&V 的 name/description/location；advisor 再新增职责提示与此次动态会话 ID。tool 名称集合相同。
- M:L4 是实际完整用户指令；M:L30 和 V:L5 是此次 advisor 的完整任务交接。两者不是同一份提示，也不是把主会话完整历史交给 advisor。
- 动态历史保存在两份原生 JSONL；没有 compaction/branch-summary/session replacement 事件，所有非空 parentId 均能在各自文件内找到。只能排除可见链缺口，不能断言供应商内部处理方式。

`svc-verification/SKILL.md` metadata.version=`16.0.0`。来源记录指向 sources/svc HEAD `0cf1406fa9b3bdd0911c5873bcbf69a976db3a5b`，当时入口和两份 references 已有本地修改，不能只引用该提交代表本次材料。冻结文件 SHA256：

|文件|SHA256|
|---|---|
|SKILL.md|3b7ecb08c1cd22bfabe2f69e328c4b4d323e52b0f83fadba6ce0fad5ea286354|
|check-design.md|351f9a5a20cae5b6aabd7c4f6e20df3bee36a4294b4a70d388429d0b82037238|
|evidence-design.md|8b907afaa58596eb85118897faa62ab63b7585581319adb8d475cec32fc1aa63|
|interpreting-results.md|c5719eab7702d6de5d2ef0f9fddc9e19f2866b985da3b689abf5700234128566|
|repeatable-checks.md|b1555848697eb0ad9842d40d2651681ad4a80241594df90c565281aea3dba36c|

该版 check-design 已包含并列对象逐个承接、非累积类别相邻正反例、跨组件真实路径、初始状态不能被自建 setup 替代等方法；interpreting-results 已要求修正定位后保留未验状态、不能用别的通过抹去反例、不能用猜测评分器代替需求。材料是否具有相关方法与模型是否执行方法是两项不同事实。

全部身份与 SHA256 的机器可读索引为 `E/identity-comparison.json`。

## 下载与保存

2026-09-30 07:25:27 UTC 完成已有登录会话的只读 `GET /runs/2ef9660d0dad/workspace/template-bundle`：HTTP 200，82,670,747 bytes，SHA256 `53d6cb2f579c116a49430b75afd21de0d75524085510988b5e77ac77176c1c5c`。CRC 全部通过；解压 1,504 个文件，无越界路径/符号链接跳过。收据与逐文件清单为 `E/download-receipt.json`、`archive-index.json`。

归档有源码、需求、数据库、原生/provider证据，未包含整个容器、`.arc`、`.git` 或官网逐例报告。文件按数据解压，未执行；含运行认证材料的证据保存在权限受限本地目录，不复制到报告。最初沙箱请求具体失败为 curl 6 / Could not resolve host: arc-bench.com；工具批准网络读取后取得上述材料。没有审批拒绝或剩余下载/登录阻塞。官方逐例失败和应用 Git 身份不可得属于证据缺口，不能以重新评测补齐本次授权。
