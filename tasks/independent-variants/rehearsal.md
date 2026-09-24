# 独立 Variant 无模型预演

2026-09-23 已使用真实 `scripts/profiles.py:resolve` 和 `scripts/native_profiles.py:materialize`，对四个活动 variant 各执行一次物化。没有调用模型、启动 Braid 或 benchmark；输入 URL 是 `http://127.0.0.1:9/factory26`，没有读取或写入 secrets。现有 native cache 可用：`/Users/lanzhijiang/.cache/factory26/runtime-faf60473273ddeed`。

可重放脚本是 [`replay.py`](/Volumes/WorkSSD/Development/factory26/runs/independent-variants/rehearsal/replay.py)，完整精简快照是 [`summary.json`](/Volumes/WorkSSD/Development/factory26/runs/independent-variants/rehearsal/summary.json)。脚本每次只重建自己拥有的 `runs/independent-variants/rehearsal/materialized/<variant>`，然后把 `resolve` 的 effective contract 直接交给 `materialize`。同一脚本支持 `--variant pi-team-vv --visual-url http://127.0.0.1:10/visual`；该分支的快照在 [`visual-route-probe/summary.json`](/Volumes/WorkSSD/Development/factory26/runs/independent-variants/rehearsal/visual-route-probe/summary.json)。

## 接口观测

`resolve` 为每组返回 schema v2 effective contract：两个 Braid 默认槽位是 `issue`、`pr`，所有 profile 都是 `adapter_type=pi`；本轮四组使用同一 SVC revision `393b9352fae1e8b22d86b28a65ff2f7ded267a38`。`materialize` 返回的 Braid `profiles`、`bindings` 和 defaults 已原样保存在快照中。每个 binding 都包含 `adapter_type=pi`、独立 launcher、`native_template`、`native_home.root`、`api_key_environment=FACTORY26_API_KEY` 和 capability digest。

Pi 原生模板的共同部分如下：

- `settings.json` 为 `packages=[]`、`subagents.disableBuiltins=true`。
- 每个模板都生成 `models.json`、Pi launcher、observer extension 和五个角色文件：`explorer`、`executor`、`browser-operator`、`vision`、`specialist`。
- 主 profile 技能始终为 `svc`、`ponytail`、`impeccable`；上下文限制始终为 soft ratio `0.8`、hard bytes `1000000`。
- `explorer` 使用 `deepseek-v4-flash` + `svc`；`executor` 使用 `deepseek-v4-flash` + `svc/ponytail/impeccable/agent-browser`；`browser-operator` 使用 visual `deepseek-v4-flash-vision-exp` + `agent-browser`；`vision` 使用同一 visual model 且无 skill；`specialist` 使用 `kimi-k3` + `svc`。五个角色均为 `reasoning=high`、fresh context。
- 默认未传 `visual_base_url` 时，`factory26-visual` 实际写入同一无效本地 URL 和 `$FACTORY26_API_KEY`。另一次 `pi-team-vv` 物化传入 `http://127.0.0.1:10/visual` 后，实际改为该 URL 和 `$FACTORY26_VISUAL_API_KEY`；分支已由 [`visual-route-probe/summary.json`](/Volumes/WorkSSD/Development/factory26/runs/independent-variants/rehearsal/visual-route-probe/summary.json) 核对，但仍不代表真实凭据或 provider 可用性验收。

## 四组实际差别

| variant | profiles / 默认 Issue、PR | 主模型 | 指令文件 | effective digest |
| --- | --- | --- | --- | --- |
| `pi-team-deepseek` | `pi-deepseek-fast` / deepseek、deepseek | `deepseek-v4-flash` | `main.md` | `7480346f9c50f7e7feda372063815083bf8a4264b6bc6fe0c1550ee006c39d96` |
| `pi-team-glm` | `pi-glm-fast` / glm、glm | `glm-5.3-flash` | `main.md` | `68e7d1e9e16a74c251c6d9d8b3e84c5d3696323dedd952edb912c7141b1e4316` |
| `pi-team-mixed` | `pi-glm-fast`, `pi-deepseek-fast` / glm、deepseek | 分别为 GLM、DeepSeek | `main.md` | `f53a9c91f703590d75226b8bb26e072bc2574e70f860d4c192e6bea6e48327b5` |
| `pi-team-vv` | `pi-glm-vv`, `pi-deepseek-vv` / glm、deepseek | 分别为 GLM、DeepSeek | `main.md` + `vv.md` | `86224c68341b8fc2f56bbb60ea7f511fdb1b0e60eb1efb217146e168fe00fb60` |

因此，单模型组和 mixed 组的差别是 profile 集合及默认分派；`pi-team-vv` 保持相同角色、模型和 skills，只增加 `vv.md` 主指令，形成新的 profile/capability digests。`glm` 模板的 text provider 因角色仍引用 DeepSeek 和 Kimi，实际模型列表为 `deepseek-v4-flash`、`glm-5.3-flash`、`kimi-k3`；DeepSeek 模板没有 GLM，只有 `deepseek-v4-flash`、`kimi-k3`。两者的 visual provider 都只有 `deepseek-v4-flash-vision-exp`。

## 迁移应保持的行为

迁移到独立 variant 目录后，仍需保持每个 profile 的公开 assignee login 与 description、`issue/pr` 默认槽位、五个 native role 的模型/工具/skills/context、主 profile 指令、Pi 原生 settings/model catalog，以及每个 profile 对应一个 binding。现有 capability/effective digest 只作为旧输入基线和诊断参照；新实现可以用其实际材料清单和哈希表达诊断，不被迫保留同名字段。共享运行设施在 Braid 依赖接口边界消费已物化的 profiles、defaults、bindings；variant 自己构造这些对象，不应重新从 variant 名称推导，也不应让一个 variant 的指令变化改写其他 variant。

## 对 technical/verification/plan 的物化核对

预演没有发现需要改变四组模型、角色或 skill 选择的事实，但有三项路径和依赖必须写进实施边界：

1. 每个 Pi profile 的 launcher 实际传入 `--no-extensions --no-skills --no-prompt-templates --no-themes`，再加载 runtime cache 的 `pi-subagents/index.ts` 和该 profile 的 `factory-subagent-observer.ts`，并只把主 profile 的 `svc/ponytail/impeccable` 作为 CLI `--skill`。角色通过各自 frontmatter 的 `skillPath` 和 `skills` 使用 `agent-browser` 等角色 skill，且 `inheritSkills=false`。因此独立目录/ZIP 必须保留五个角色文件、profile skill root、observer 和 `pi-subagents` 运行依赖；不能只复制主指令和 SVC 正文。
2. 实际物化还生成 invocation 级 `bin/agent-browser` wrapper。它依赖 runtime cache 的 `agent-browser` CLI 与已安装 Chromium，要求 `PI_SESSION_ID` 或 `CODEX_THREAD_ID`，并把状态/socket 分别放在 invocation 的 `browser/<hash>` 与 `b/`。计划中的 variant-owned browser wrapper 需要保留这些运行时路径和身份隔离；当前预演没有启动浏览器，路径重基和制品是否携带 Chromium 仍待独立包验收。
3. 当前 lock 的直接依赖版本是 `@earendil-works/pi-coding-agent 0.85.1`、`@openai/codex 0.155.0`、`agent-browser 0.38.1`、`pi-subagents 0.56.0`。开发物化引用 `/Users/lanzhijiang/.cache/factory26/runtime-faf60473273ddeed` 的 runtime cache；新 build/run 需要明确把 `pi`、`agent-browser`、`pi-subagents` 和 Chromium 的制品路径重绑定到独立包或已批准的共享 runtime。当前证据不足以决定是否可以从 Pi-only 制品删除 Codex 依赖，交给打包黑盒验收确认。

其余计划项与物化证据一致：`models.json` 必须按主 profile 加五个角色的模型并集生成，`settings.json` 禁用 builtins，所有 profile 指向同一 invocation application workspace；真实 Braid 请求、独立 ZIP、Linux Runner、浏览器启动和模型协作仍未覆盖。

## 尚未覆盖的真实验收

本预演只证明现有 resolver 到 native files 的接口链路和当前输入基线，尚未证明：独立目录移走其他 variant 或共享生成器后仍能构建；只修改一个 variant 后其他三个无需重生成；package/官方 Runner 入口仍可执行；Braid 实际接受请求并分派 Issue/PR；Pi provider、browser、sub-agent、SVC skill 真实运行；真实模型生成、交付、ARC/benchmark 结果；以及带真实 `visual_base_url` 的视觉凭据路由。
