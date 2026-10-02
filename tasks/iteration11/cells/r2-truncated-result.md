# R2：原生子代理截断结果不能返回完整成功

状态：源码修复与补丁/语法核对完成，未构建部署、未进行真实调用验收。用户授权继续闭合 I11 R2，允许必要修复或有据不改；本单元未启动模型、实验或 I10恢复，未运行测试/探针，未提交。非唯一编辑者，本次只追加共享结果处理hunk及其runtime指纹目标，未改变I11-05已有完成屏障逻辑。

## 定向证据与根因

冻结来源为 `tasks/iteration11/run-audit/github/snapshot-01/`，根native-home为 `work/native-homes/pi-glm-fast-01a0eb68-19b6-7c30-91d6-bd339f346335/`：

- `subagent-artifacts/1657f14b-e00e-433e-88c2-f9ba59cc0c83_vision_transcript.jsonl` record 102保留 `stopReason=length`、`rawStopReason=length`，回答在跨图疑点“2. 文件名与画面内容不符”下一行的列表标记处停止。输出usage为16,385，其中reasoning为5,028；该子任务先前读取27张图的事实沿用已完成原生审查，本次没有重读图片。
- 同home `2026-09-29T04-24-34-972Z_01a0eb68-479c-72ef-b9ea-288545453828.jsonl` 原始L9是 `custom_message`，正文直接称 `Background task completed: **vision**`，随后交付截断文本，没有length或不完整提示。这比“父可能没看出截断”更具体：原生返回把该结果标成completed。
- 子实际session `.../2e9be486-eef5-4078-a735-f0ede9700bd4/run-0/session.jsonl` L49包含同一末尾assistant与length。不是审查工具展示截断，也不是图片读取失败。

锁定pi-subagents 0.56.0中，前台`runs/foreground/execution.ts`及后台`runs/background/subagent-runner.ts`都在进程正常退出后调用共享`detectSubagentError(messages)`；该函数只扫描末次有文字assistant之后的toolResult错误，不检查assistant的length终止。`getFinalOutput`又将length文字当普通最终输出。由此可以同时得到非空结果、exitCode=0与success=true，后台notify据success展示completed。当前I11的生命周期修复没有改变这一判定。

这是一处原生结果返回契约缺陷，不能通过Braid解释图像业务或给vision多加“请完整回答”来修。截断只说明回答未完整生成，不说明已经读取的图片无效或应用视觉验收失败。

## 最小改动

在现有 `harness/npm/patches/pi-subagents-0.56.0-completion-boundary.patch` 追加 `src/shared/utils.ts` 的两个窄分支：

1. `getFinalOutput`检查最后一条assistant；若`stopReason=length`，保留其全部已有text并加前置“结果不完整、按需仅补缺失部分”的提示。提示进入父可见正文，而不仅藏在原始transcript或details中。
2. `detectSubagentError`对同一最后assistant返回既有`hasError=true/exitCode=1/errorType=response`及准确length原因。前后台继续使用现有failed/error路径，不增加partial状态机，不把该结果标为完整成功。

只看最后assistant：历史曾length但后来同次执行有成功续答时，不会因旧length判失败。原有toolResult错误扫描保持原样。原始transcript、已生成文本、session及artifact入口保留；是否再调用补齐由父判断。即使length正文为空，前置提示仍为可见输出，避免被原有“no output/cold-start”路径解释成需要自动重跑。

已追两条调用链的重试判断：新的`response failed (exit 1): ...`沿既有tool-failure前缀排除模型fallback；startup retry亦要求无错误、无消息、无用量等零活动证据，本情形不满足。本改动不新增自动重试、换模型或重读27图。

Factory observer不改。其恢复展示读取原生result的success/state和metadata exitCode，修正后的失败事实自然沿原有路径显示。`association_status=partial`与`diagnostic_status`表示证据关联/索引完整性，不是模型回答完整性，不能复用这些字段来掩盖原生结果的success误判。observer也不应从回答内容或字符数猜是否截断。

## 构建接线与核对

- `scripts/runtime.py`仅为completion-boundary patch的`target_names`追加`src/shared/utils.ts`，使缓存指纹覆盖新目标；未改其它I11-05入口。
- Linux `submission/Dockerfile`本就应用同一完整patch，无需第二条安装命令。acceptance-off patch不修改utils，按当前构建顺序串行应用不会覆盖本修复。
- 在锁定0.56.0缓存源的临时文件副本上，completion-boundary和acceptance-off两个patch按构建顺序以`--fuzz=0`应用成功；实际缓存未改。
- 修改后的utils通过已有darwin-arm64 esbuild的TypeScript语法转换；runtime.py通过内存语法编译。没有调用生产函数、模型或行为测试，也不是完整类型检查或打包验收。
- patch文件中的上下文“空格+tab”为标准unified diff格式；关闭仅针对该格式的space-before-tab检查后diff检查通过。首次语法工具路径不存在，改用同一已安装依赖内的esbuild二进制后通过，未安装依赖。

## 关闭边界

R2从“返回契约未核清”推进为“确定根因已修，未部署／真实采用待验”。下一次已授权运行若自然出现length，应看到父正文的不完整提示、failed/error及已有部分内容，不能再显示completed；后来真实续答成功不应被历史length污染。没有自然length时保持未触发，不为补证新增实验或回放模型。

本修复不保证父一定正确使用部分观察、不补造截断后的尾部、不改变图片角色/模型或业务验收。既有结构化产物若已成功产生仍保留；尾部回答length必须如实披露，产物是否足够由消费者判断。
