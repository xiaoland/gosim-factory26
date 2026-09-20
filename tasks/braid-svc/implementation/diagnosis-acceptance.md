# 诊断入口独立验收

验收范围：只从 `factory.py` 与 `playground.py` 的用户入口开始，并按入口给出的路径读取失败页面、官方测试和冻结应用源码。没有读取 task packet、既有报告、实现者总结或完整原生 rollout；没有调用模型或平台，也没有运行 benchmark。

## 实际命令

```sh
cd /Users/lanzhijiang/Development/factory26
python3 scripts/factory.py list
python3 scripts/factory.py --help
python3 scripts/factory.py show 20260920-141339-6138c072 --eval 20260920-163747-e5039d --case REQ-2.2
python3 scripts/factory.py show 20260920-141339-6138c072 --eval 20260920-163747-e5039d --case REQ-2.2 --json
rg -n -C 4 'noteEditor|fillComposer|Note editor|Create Note' third_party/arc-bench/arc-bench/webapp/keep/tests/helpers.ts third_party/arc-bench/arc-bench/webapp/keep/tests/REQ-2.2.spec.ts
sed -n '740,805p' runs/20260920-141339-6138c072/application/public/app.js
sed -n '315,345p' runs/20260920-141339-6138c072/evaluation/20260920-163747-e5039d/test-results/keep-tests-REQ-2.2-REQ-2-2-Create-Note-chromium/error-context.md
jq '{task, status, benchmark_revision, started_at, generation_finished_at, workflow, backend, versions}' runs/20260920-141339-6138c072/run.json
jq '{"public/app.js": .["public/app.js"]}' runs/20260920-141339-6138c072/application-hashes.json
git -C third_party/arc-bench rev-parse HEAD
git -C third_party/arc-bench status --short
python3 scripts/playground.py status 2041e4b58701 --saved
python3 scripts/playground.py status 23a11724c9f4 --saved
```

## A. REQ-2.2

`list` 将该 run 显示为 `pi-svc-braid`、已生成，所选评测 `20260920-163747-e5039d` 已完成，得分 14/32。指定 case 的 `show` 直接给出了超时位置、页面片段和四类附件，因此不需要先读取 native rollout。

### 失败层、预期与实际

失败发生在浏览器可访问性定位层，而不是应用启动、打开编辑器或标题输入框不存在的层。

官方测试（run 记录的 `benchmark_revision` 为 `1eb018367bedd618d3b9ced406ce07fb423d4956`；本地官方工作树 HEAD 相同且干净）中：

- `REQ-2.2.spec.ts` 调用 `createNote()`，随后断言新笔记可见。
- `helpers.ts:233-240` 将编辑器定义为 `getByRole('dialog', { name: /^Note editor$/i })`，再在该 dialog 内填写名称为 `Title` 的 textbox。

实际评测在 `helpers.ts:240` 等待该父 locator 60 秒后超时。`show` 提供的失败页面片段显示：

```text
dialog "Create note"
  textbox "Title" [active]
  textbox "Note content"
```

冻结的 `application/public/app.js:763` 也明确将创建模式的 dialog 设置为 `role="dialog"` 且 `aria-label="Create note"`；同一文件 `:783` 将标题输入框标为 `aria-label="Title"`。因此，最受证据支持的假说是：点击“Take a note”成功且标题框已出现，但父 dialog 的可访问名称为 `Create note`，不匹配官方测试所需的 `Note editor`，使后代 textbox locator 从未开始匹配。

### 竞争解释与下一项区分检查

1. 官方测试的可访问名称可能与产品需求契约不一致。已确认测试源码与 run 固定的 benchmark revision 一致，所以不是当前 checkout 漂移；本次按范围没有读取 task packet，不能替产品规范裁定哪一个字符串应当正确。
2. 冻结应用源码可能不是 evaluator 实际服务的字节。页面证据与源码都显示 `Create note`，因而该解释较弱；但 `show --json` 的 `evaluation.application_sha256` 为 `null`，不能完全排除。
3. 这可能是瞬态渲染或另一个 dialog。超时时的 accessibility snapshot 已同时显示 `Create note` 和 active `Title`，且源码的创建分支固定设置该名称，因而较弱。

下一项最小区分检查是在同一评测应用副本中只打开 composer，并记录两个精确 locator 的 count（`Note editor` 与 `Create note`）及被服务的 `public/app.js` SHA-256。前者区分名称契约/瞬态问题，后者区分冻结源码与 evaluator 产物。若要裁定产品契约，再读取同一 benchmark revision 的需求定义即可。

### 入口体验

可以通过少量定向阅读形成上述判断：一个 `show` 输出已同时给出失败 locator、实时页面树和附件；随后只需读取官方 helper 与冻结的对应 DOM 构造。入口没有迫使我拼接完整 rollout，也没有把这个 timeout 误导成“标题框缺失”。

一个具体缺口是来源可追溯性：`show --json` 已暴露 run 的 `application-hashes.json`（其中 `public/app.js` 为 `bd45d7a74ec225fec1b24d1017f606038d3062debc9e90717e1bd46c9bca57bc`），却将该 evaluation 的 `application_sha256` 输出为 `null`。建议在 case 输出旁显示 evaluator 实际服务的源码哈希及其验证状态；否则“冻结源码造成页面行为”的因果链仍需保留条件。

## B. 保存的 playground 状态

| ID | 保存记录中的历史进展与终态 | 心跳 | 时效与可追溯性结论 |
| --- | --- | --- | --- |
| `2041e4b58701` | `terminal: true`、`status: FAILED`；0 通过、135 失败，135 个均为 `timedOut`；末条进展事件为 `2026-09-20 08:23:28` 的 error，摘要为 runner 以测试失败或运行时错误退出。 | 有末条心跳：`2026-09-20 08:23:03`，`Still working: Test progress 0/135`。它说明终态前最后保存的进度，不能解释每个超时的具体原因。 | 两个 observation 的 `observed_at`、`age_seconds` 都是 `null`，`freshness` 是 `unknown`，因此只能判断“保存记录声称已终态”，不能判断该记录的新鲜度或当前外部执行状态。traceability 显式为 `empty`，producer/version 均为 null，interfaces/tests 都为 0。 |
| `23a11724c9f4` | `terminal: true`、`status: PASSED`；1 通过、0 失败、100%。末条进展事件为 `2026-09-20 08:21:30` 的 success，摘要为提交成功。 | 输出没有 `last_heartbeat` 字段；不能把字段缺失解释为从未发送心跳。 | 同样只有保存记录的终态，freshness 为 `unknown`；traceability 同样 `empty`，没有生产者、版本、接口或测试链接。 |

`--saved` 的输出在时效问题上是诚实的：它明确报告 `unknown`，没有把旧的事件时间伪装成新鲜度。它也明确报告 traceability 为空，因而不能从这两条状态建立“某个接口/测试导致终态”的因果链。

## 未决/阻塞（最多三项）

1. REQ-2.2 的产品级 dialog 名称契约未在本次范围内读取，故不能判定是应用实现违约还是 benchmark 测试契约错误。
2. evaluation 没有记录实际服务应用的哈希，冻结源码与评测页面只有强相关证据，尚非可验证的同一产物证明。
3. 两条 `--saved` 状态都没有观察时间、年龄或非空因果 trace，不能判断保存状态的新鲜度，也不能追溯终态根因。

## 建议

建议 **revise**：诊断入口已经足以快速定位 REQ-2.2 的可访问性名称失配，且保存状态不会虚构时效或因果；补上 evaluation 源码哈希和 playground 保存快照的观察时间/非空 trace 链接后，才能让上述判断从“有条件的诊断”变为可审计的结论。
