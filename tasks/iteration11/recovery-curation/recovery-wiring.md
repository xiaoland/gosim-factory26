# GitHub 摘剪副本以 I11 本地接续

本次只修改恢复入口，未打包、恢复副本、启动模型或运行测试。两个 Python 文件通过内存语法编译。主线负责冻结最新 I11 基包、摘剪副本 ZIP 与 Linux Braid 制品，然后执行恢复。

## 决定与边界

原入口不足：原生刷新白名单缺少 `pi-braid-i11`；刷新后又把旧 models.json 整份覆盖回来；仅更新 user_instructions，未更新 Profile 的 context_window_tokens 或 root_check_messages。现已接入 I11，使用基包当前模型定义与本次环境中的 URL/key 引用，刷新完整 Profile（只允许 user_instructions/context_window_tokens 差异），并刷新根检查消息。当前 I11 两个 profile.json 与原现场对应 Profile 的既有字段一致，模型、reasoning、身份不变。

`--base-package` 必须是主线从当前 I11 源码完整构建的包。`--refresh-native-materials` 只从开发树额外替换 collector、observer 与顶层 instructions；run.py、模型、角色、skills 和运行时仍来自基包，不能将旧包加此开关解释成完整升级。恢复使用当前 base URL，不保留旧模型路由覆盖；需要独立视觉网关时同时提供 VISUAL_BASE_URL 和 VISUAL_API_KEY。

原 `braid-request.json` 的 state 为 `/workspace/template/.factory26/20260929-042409-1202e245/braid-state`。官方 local_submit.py 的 output/template 路径同为 `/workspace/template`（主线已核实）。新容器用这个 output，不能改成宿主机路径；原容器保持暂停，副本在独立新容器使用相同容器内路径即可。恢复入口仍拒绝路径迁移，不批量替换数据库、Git 或原生历史中的字符串。

## 原生上下文如何重建

不能把 offline-resume 等同 fresh。这里依赖最新 Braid 的既有机制：`group/provider.rs::materialized_profile_with_binding` 将 Profile 与 binding 的有效材料散列成 revision；`group/worker.rs` 在恢复时发现 Profile/instruction revision 不同，调用 `begin_provider_replacement`；`group/dispatch.rs::materialize_context_reset` 从摘剪后的当前 Issue/PR canonical context 重新创建会话。工作项、负责人、工作树与未提交文件保留。sleeping 会话也必须同时满足 Profile、context、instruction revision 一致才会原生 resume，本次 I10→I11 指引变化使它在再次激活时重新创建。

Braid 当前 offline-resume 身份检查只豁免 user_instructions，尚不豁免 context_window_tokens。恢复入口备份 `braid-state/request.json` 到 `recovery-source-state-request.json` 后，只迁移该窗口字段；不改数据库里的历史 Profile revision。原顶层请求另存为 `recovery-source-braid-request.json`，然后用当前 Profile/bindings/root_check_messages 执行。保留原 prompt 作为运行身份；最新角色指引与根检查消息生效，不伪造从零规划过程。

本次不删除旧 native homes/session 文件；它们保留为历史证据，原 `native` 归档入口移名为 recovery-source-native。当前活跃会话重建依据材料 revision 变化，不把历史日志拼进新模型上下文。运行后主线应从新的 physical/session.json 与 context_resets 的记录确认实际 replacement 和 canonical context；本次只完成静态调用链核实，未声称已经运行成功。

## 代码与路径保持

解压保留 `.git` 与未提交文件；已有 `.git` 的工作树跳过 Git 修补。只有缺少 `.git` 时才通过 origin 重建索引，使用 read-tree 而非 checkout，不能恢复平台已遗漏的未发布提交历史。摘剪 ZIP 必须保留符号链接类型、模式、Git 与 SQLite/WAL，且只保留一个目标 `.factory26` run。

原入口会在恢复到已存在的 output 中写入归档文件，因此主线须使用新容器的全新 template，不能覆盖旧现场。恢复时只刷新 harness 的 skills/capabilities、Pi/PBB 启动器及其路径，保留 application/origin/worktrees。补齐与 I11 generate 相同的 portless 与包缓存环境；最终交付仍走原 export_delivery/deliver。

## 执行接口

先将三个大写文件路径替换为本轮冻结产物；这是打包命令，不会调用模型：

```sh
python3 scripts/package_completed_recovery.py \
  --source-run-id pi-braid--hackathon--github-7fe42a1248f9d8 \
  --workspace CURATED_GITHUB_WORKSPACE.zip \
  --base-package CURRENT_PI_BRAID_I11.zip \
  --braid CURRENT_LINUX_BRAID \
  --braid-source CURRENT_BRAID_SOURCE.tar.gz \
  --output I11_GITHUB_CURATED_RECOVERY.zip \
  --continue-generation --refresh-native-materials
```

上述 workspace ZIP 中的请求必须仍是 `template/.factory26/20260929-042409-1202e245/braid-state/request.json`。恢复包由既有本地 runner 在新容器中展开，runner 调用接口保持：

```sh
python3 main.py /workspace/template/requirements --output-dir /workspace/template --type web
```

模型凭据只由本地 runner 环境注入。禁止上传或使用从零生成入口；本次结果标记为人工摘剪的 I10 成果以 I11 接续，不作为 I11 从零生成成绩。
