# Rust 实时资源采集与 V8 分配证据

用户在独立侧会话授权：“是的，按此拆分采集器；并且接入 V8”。本任务迁移实时 cgroup/进程/PSS 采样与资源监督到 Rust，Python 保留装配和离线关联；为原生 Pi 提供进程内 V8 内存分类、GC 与有界分配采样。不操作主线程当前运行、不联系其子 Agent、不 commit/push、不运行 Factory/Braid 测试。

保留既有资源证据结构、PID 出生身份、有限日志、事件前样本、PSS 轮转与失败原文。真实资源边界和 OOM 失败语义不变；不以新语言声称已降低整个 Python 入口开销。V8 采样不暴露调试端口，不取完整 heap snapshot；采样窗口覆盖已回收对象，否则不能解释启动临时分配。源码、编译与独立正常服务反馈分别记录，不在本侧部署到主线程。

实施面：sources/resource-monitor；公共 runtime 生产/装配/安装；harness_services 与 OTLP 资源接线；共享 native-managed 的 V8 观测模块和原生生产清单；现行资源职责说明。当前共享工作区有大量其它任务修改，按当前内容局部编辑，保留并行变更。

当前状态：实施中。完成依据为 Rust 编译、Python/JS 语法、实际独立 Linux 正常服务的采样及关闭反馈、真实 Node 分配采样落盘与开销说明。当前运行实际采用需主线程后续统一部署，本任务不发起接续。

## 已完成与交接

Rust 实时监督/采样源码已完成，公共 Linux 生产（Docker 与 derive-linux）、公共装配/安装和所有 ResourceEvidence 调用入口已接线；Python 只保留生命周期连接及离线分析。V8 模块在 managed Pi 导入时记录分类/GC，显式窗口可采样分配（包含已回收对象），新增只读 `tooling/scripts/v8_profile.py` 汇总归档。保护仍核对实际 cgroup 限额/OOM，入口 PID/starttime/父进程/PGID 身份在信号前重新核对；没有新增启动压力门禁。

独立 WSL development-1 正常文件服务实际 exit0，24次HTTP访问，模型0；Rust guard及按需采样均正常 final，资源读回无错误。guard中位collection约1.61ms，sampler-only约2.06ms。实际 Rust guard PSS约1.7～2.8MiB，RSS约2.7～3.4MiB；不能据此宣称整个 Python 控制入口已消失，不能将小负载延迟与I15高负载直接对比。原始 getrusage peak约19MiB与进程VmHWM不同，最终源码主峰值改用本进程/proc status VmHWM，getrusage原字段单存，不拿它估算Rust自身常驻开销。

同一正常服务V8产生14个分类样本、3次GC、8秒分配采样正常保存，样本估算约6.30MB；它证明采样链可用，尚未解释真实Pi的500MiB恢复峰值。原件归 `runs/rust-resource-v8/evidence`，摘要 `v8-summary.json`；Linux生产日志 `production.log`，当前最终二进制交付 `delivery/factory26-resource-monitor`。

用户随后要求“加速加速，时间不多，可以省去很多验证、校验”：省去重复服务运行、整包校验、负载矩阵和额外覆盖检查，保留Rust编译、Python/JS语法和上述已取得实际服务反馈。最后的峰值口径/出生身份字段补充只编译生产，不另跑服务。未进行Factory/Braid测试、模拟探针、主运行接续或commit/push。主线程后续通过正常执行器统一生产/采用新runtime，不能向旧二进制热插采样源码。
