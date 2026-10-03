# 制品、遥测与恢复证据

本页对应 artifacts.py、telemetry.py、analyze.py、checkpoint/prepare producer 以及制品相关 CLI。

制品以 artifact_id 和 manifest 身份发布。export/transfer 先认证引用摘要和来源身份，再核验收到的字节；失败的 staging、源材料和未确认半成品保留。重入使用原请求身份和目标回执，不因源暂时不可读而重复发布。

retain、GC 和清理共享稳定的保留意图。目录名、completed、单独 hash 或 Git 提交不能证明可回收。未知位置、旧 store、缺少保全条件和未确认 owner 的材料继续保护。

telemetry 保存 stream、epoch、源序列、原始 protobuf、错误和封口事实；同源批次摄取幂等，冲突原件保留。analyze 固定原件摘要和观察截止点，不能从批次数推导 token、费用或语义进度。

checkpoint/prepared 与来源停止证明分开发布，必须保存来源执行身份、实际路径和 OS/架构/runtime/logical root。缺少 Git/native/外链或连续停写证明时保持 partial；历史 schema 按原冻结合同解释，不用新布局追认完整恢复。

v3 定义换版通过 repair 的 `definition_assets` 声明已有 name、新 artifact reference、member 和可选解析 store；同一物理资产中的嵌套角色须保持一致引用与成员关系。`--artifact-store` 指定目标解析位置，prepare producer 按需传输并核验字节和实际装配；同 store 复用，不要求操作者重复 transfer。物理 store 不进入内容身份，不能用目录名或旧路径代替引用。

目标保持同一 OS、architecture 和 logical run root，并明确 runtime identity。当前 runtime 换版要求 `bin/braid`、`native-managed.mjs` 和 Pi 的 package.json 与来源摘要一致，以保留原 Braid、native hook 和 Pi 协议；不能借此迁移会话协议。Local 不覆盖仍被旧定义占用的逻辑位置，Docker 可在独立 namespace 保持相同逻辑根。变更关系和实际 readback 保存到 prepared，prepared 不携带停止或启动许可。

## 传输、遥测和 Harness

同盘发布使用隔离写入的 clone；不支持 clone 或跨文件系统时复制字节，不共享可写 hardlink。terminal staging 先记录请求、来源和内容身份，再 rename 到发布位置；重入复用原 artifact。Docker 下载和 ARC SDK transport tar 只有在最终内容核对、耐久保存和 verified 回执成立后释放 scratch，未归属 metadata 和旧半成品保留。

telemetry snapshot/batches/export/ingest 保留 stream、epoch、源序列、原始 protobuf 和错误；同源批次幂等，冲突原件保留。runner 持有 ResourceEvidence，Docker 读取负载 cgroup 样本，不以 OTLP 开关代替资源证据。analyze 固定原件摘要和截止点；没有调用身份时，token 和费用为 unknown。

四个新 I14 Harness 将冻结定义、运行派生输入和可写 state 分开。checkpoint/prepared schema 3 保存 state 与定义依赖的 artifact reference/member，不重复携带 runtime；target layout 同时约束 `run_root`、OS、architecture 和 runtime identity，runner 还会校验实际 logical root 与 definition mount。历史 schema 1/2 仍按自包含合同读取。SDK 自包含交付仍保留原导出树和 inventory；终态归档只有在容器路径映射和内容身份成立时才可省略定义副本。

`submission/exp_checkpoint.py prepare` 是 prepared v3 的底层 producer；它接收 checkpoint、target layout、repair，并可用 `--artifact-store` 指定定义资产的目标 store。`--execute-prepared` 属于独立交付包入口，消费已完成的 assembly，不是 `python -m lab` 的恢复动作。
