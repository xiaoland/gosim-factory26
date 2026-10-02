# Pi 配置根与原生会话目录分离

用户授权“现在可以启动 I12（考虑从0重启了）”。本次完成启动前必要的窄修复，依据 [根因复核的 native 节](root-cause-review/report.md#native缺-headeruser-源于活动会话被迁移不能只修采集器) 和 [四组双段对应表](root-cause-review/native-split-correspondence.json)。主线负责 Linux 构建、冻结、从零启动和真实运行取证；本记录不把编译当行为验收。

旧 adapter 把同一物理会话 home 同时作为 `PI_CODING_AGENT_DIR` 和 `--session-dir`。已有证据表明，继承配置根的子 Pi 启动会把根目录有头 JSONL 迁入 `sessions/<encoded-cwd>/`，父进程却在原路径继续追加，留下有头前段和无头后段。四组记录链可连通；这不等于已经证明模型失忆。

## 实现与可观察契约

仅修改 `sources/braid/src/provider/pi.rs` 和 `sources/braid/src/provider/factory.rs`。

有物理会话 home 时，Pi 配置、模板和子代理环境仍使用该 home，新的显式 `--session-dir` 改为 `home/sessions`。父活动 JSONL 不再写到配置根顶层，避开已观察到的 Pi 启动迁移范围。adapter 未配置 home 的既有工作区会话目录保持原规则。启动日志分别记录 native_home 和 session_dir，便于核实际进程边界。

Braid 会话身份、`native_session_path` 仍来自 Pi RPC 的实际 sessionFile，manifest 不构造猜测的新路径。恢复仍优先使用已有准确绝对路径，传 `--session` 后核 Pi 返回的是同一文件；在当前配置根中的文件沿既有 native-home 定位。对于当前配置根之外的嵌套绝对路径，恢复现在从 `sessions` 的父目录取得配置根，避免把会话目录当配置目录；旧平铺文件仍按原文件父目录定位。没有重命名旧文件、覆盖历史身份或引入迁移层。

现有 `src/evidence.rs::native_source` 按保存的绝对 `native_session_path` 读取 Pi 文件；分析入口已有按 native session ID 在 home 内关联同名分段的读取逻辑。因此目录分离不要求归档字段或消费者改动。旧双段原文件和对应表保持可读、原样保留，本修复不自动拼接双段、不把无头后段伪造为完整会话，也不宣称已解决旧损坏现场的冷恢复。

## 编译与剩余证据

2026-09-30 在现有本地 target 完成一次 `cargo check`，退出码 0，仍有 13 个已有 unused/dead_code warning。日志为 `/tmp/factory26-native-directory-check.log`，`git diff --check` 通过。本地没有第二轮扩张修复，没有编写或运行测试、smoke、模拟探针、Pi 进程或模型调用；未修改第三方 Pi、对象指派、共享 provider 指引、variant、部署和原始运行现场，没有提交。

下一次获授权真实运行中，在父 Pi 首次实际启动子 Pi 后，核父 manifest 的准确路径位于新会话目录，文件仍包含同一 session header、初始 user 及连续 parentId 链，没有在配置根顶层生成同一父会话的增量后段。若自然发生恢复，再核同一 native session identity、配置根和真实绝对路径，不为验证而额外制造模型执行。旧平铺或双段会话若需要冷恢复，应先取得完整原生链与路径证据；本次从零启动不依赖该未经验证的历史恢复分支。
