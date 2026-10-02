# I10成果保留与I11接续上下文整理

用户授权：完整保留I10生成代码、原生会话、Issue/PR等原始结果；另行摘剪、整理到相对干净状态，尽量保留生成进度，作为I11未来接续起点。用户现已授权I11从GitHub摘剪副本本地接续，使用自有API，单题前20分钟每5分钟取证检查。

## 执行边界

原始I10两容器保持暂停，原工作区只读取，不删除评论、会话或未提交文件。
先完整归档，再制作独立整理副本。保留完整Git和各工作项未提交代码；不将最新代码搭配未经核实的旧数据库。
优先采用最新成果加重新整理的上下文，不机械回退历史时间点。
原生旧会话作为证据保存；未来接续需让新会话消费整理后的当前上下文，不能简单重放旧噪声。具体恢复机制在应用前核实。
Issue/PR保留身份和真实完成状态，先精简正文、以有理由hide退出过期重复评论；合并信息不等于伪造Git合并、关闭未完成工作或提升验收声明。
裁剪后仍保留需求来源、现行决定、未决、代码位置/提交、验收适用范围、剩余责任和原始证据入口。
本操作是人工整理的接续实验起点，不作为I11从零生成的成绩。

## 分工与下一步

- GitHub负责人：github_run_status，材料归github/，给出逐项整理正文与评论取舍，核对代码保留点。
- Sheet负责人：sheet_run_status，材料归sheet/，特别消除重复无动作确认、保留契约演进的有效决定。
- 主线：完整归档和副本准备、统一应用与恢复边界；主对话继续与用户迭代I11。

当前（2026-09-30 10:03 CST）：两题均已恢复真实生成。GitHub 新原位 attempt `github-0d0cb6e9982fc1` / `f26-continue-0d0cb6e9982fc1` 使用 `d76d65f…`，保留 `github-5c52a331ef0d5c` 的实际 workspace；三项原 blocked reset 均 applied，root/PR22/Issue10 新 Pi 身份已于09:59取得真实 assistant。root 已调用并成功读取评论 #331/#332，DB投递均为delivered；本轮握手实际123–129秒，证明此次冷启动不能由旧30秒窗口覆盖，但不把某一处初始化耗时单独当唯一原因。旧失败 attempt 结论保留。Sheet `sheet-396538bc0dda96` / `arcbench-local-c4e461e6ada9` 继续使用旧 `3056feb7…` 有效生成，不为对齐版本打断。新watch首条均真实定位DB且无blocked owner：GitHub 2 active/6 pending；Sheet 1 active/21 pending。观察脚本PID分别1698832/1698834，输出在WSL `runs/iteration11/runtime-stalls/watches/{github,sheet}/watch.jsonl`。两题均未据此宣称最终交付；原I10仍暂停。

## 2026-09-29 接续实施

已核实先前实际完成的是完整归档、副本与摘剪建议，未应用摘剪。此次先落实GitHub正文/评论整理，保留所有代码与未提交进度，再用最新I11和刷新材料接续。Sheet与两个原I10容器保持暂停；无需等待Sheet整理。

冻结完成：接续包 `runs/iteration11/20260929-feasibility/agent.zip`，SHA256 `78f5f53e746a1baad8a3f6e41cfd66f0632477ecf575fea6a8170248431fe1c5`；mode=workspace-resume，refresh_native_materials=true。原需求yaml与WSL当前公开需求哈希相同（bdc17d23…）。最新Braid二进制eda9d88d…；恢复来源和材料身份在同目录recovery-source.json。

## 已发起的本地接续

WSL目录：`/home/yyh/Development/factory26/runs/iteration11/20260929-feasibility/generation`。
唯一run：`pi-braid-i11--hackathon--github-65b879cdc68a1f`；`started_at=1790691530.925718`。Runner已进入running，仍须核实解压/恢复和新Pi会话，不能将控制器running当作恢复成功。
沿用自有4020供应商网关，4GiB/2CPU，无Sheet、无官网提交、无本地评分。readable-cli接管实际Braid启动后5/10/15/20分钟SSH tar+scp取包及原生行为检查；观察写 `local-observation.md`，原始证据落 `runs/iteration11/20260929-feasibility/observations/`。

## 恢复故障修正（已授权）
用户明确要求可随时推进恢复缺陷修复。原I11现已停机保留；最新核对根Issue1仍OPEN且blocked，Issue6已CLOSED、PR16已MERGED、PR20旧assignment已retired且有新会话，不能机械重试历史四条reset。readable-cli负责仅在offline-resume中恢复仍有效、未创建新物理身份的失败reset及原始错误保留；final_product_methods负责一致归档与新恢复包，主线负责部署接续。原I10不动。修复以根恢复真实执行为验收，不以编译通过作恢复成功。

## 2026-09-30 00:16 CST 进展
冷接续run `pi-braid-i11--hackathon--github-f402061b5bc88f` 仍running。根原blocked reset已经applied，有真实模型响应；随后自编辑重建+continuation再次成功。只恢复根，未复活已关闭/合并/被替代的历史reset。
PR19/20/21现均MERGED、Issue7/9均CLOSED；根正文记录develop=e5110cb，main=2914d2d。剩余Issue10/M6b（评审、行内评论、reviewers、合并与关闭/重开）已指派deepseek-21，真实session正在读需求/契约/测试与设计；尚无对应实施PR，也没有最终develop→main整合PR。局部测试数字不当成最终应用验收。
新缺陷：Issue10 advisor默认gpt5.5触发OpenAI401，显式factory26/kimi-k3也失败（细因待查），随后请求explorer。analytics_executor负责仅I11配置/路由定位及必要修复，材料advisor-routing.md；不自行换配方、凭据，不改生成应用。

## Sheet 接续授权与交付范围

用户“好，那么将sheet也推进吧”授权本地 I11 Sheet 接续，沿用自有 API、4 GiB / 2 CPU，不做本地评分。三入口摘剪已完成，保留全部评论和原始代码：根 Issue、Issue #4、PR #13 的正文仅收敛当前任务、证据范围和剩余事项。PR #13 仍 OPEN；已有 68 项 E2E 通过不等于完成最终验收。curated DB 与变更依据见 sheet/packet.md，启动身份见 sheet/launch.md。advisor 路由调查独立推进；未证实的修复不进入冻结包，也不继续作为 Sheet 启动前置。
