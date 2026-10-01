# 本地进程身份实现与实际读回

2026-10-02。本项沿用用户“同意，开工，可以自有提交”的设施实现授权。改动仅在本地身份解释与门禁，不部署到现行控制器，不改写历史身份记录，不启动、停止或恢复实验。任务 packet 和总体设计由主 Agent 维护。

`lab.control.process_identity(pid=None)` 读取本机 `host`、`boot_id`、`pid` 和 `process_start`；默认 PID 是调用者自身。Linux 的 boot UUID 与出生 tick 来自 `/proc`。Mac 的 boot UUID 来自 `sysctl kern.bootsessionuuid`，出生秒与微秒来自系统 `libproc` 的 `PROC_PIDTBSDINFO`，结构布局依据本机 SDK `sys/proc_info.h`，使用 Python 标准库 ctypes。读取失败保留空事实及具体 `boot_error` 或 `process_error`，不制造出生身份。

`process_state(record)` 返回 `alive`、`lost` 或 `unknown`，`owner_state` 直接复用它。同机且正整数 PID 确认不存在时返回 `lost`。PID 存在时，boot 和出生身份必须非空并可比较；相同为 `alive`，同一 boot 下出生不同为 `lost`。记录缺宿主、宿主不同、PID 非法、查询权限或事实不足，以及 boot 不同都为 `unknown`。历史记录不回填。本机旧 controller 记录的空 boot/出生字段不再相互匹配；旧 worker 只有 pid/出生而没有 host，无法证明记录属于本机，即使本机该 PID 不存在仍为 `unknown`。

新 controller 和 worker 都通过共享 API 保存完整身份。retry 分配与 cleanup 只在已启动 worker 的身份为 `lost` 时继续，`unknown` 阻断动作；没有 PID 且从未启动的 attempt 不需要解释一个不存在的 worker。cleanup 也阻断未知 controller。取得实验文件锁后，仍标为 running 的旧 controller 必须确认 `lost` 才可登记新 controller，文件锁释放本身不能证明旧执行已经退出。reconcile 展示共享三态，不把空值比较写成 alive。status、wait 和控制请求原本经 `owner_state` 消费身份，无需复制新的判定；未知身份保持未确认。等待回执单列 `owner_state`，不将未知身份自动解释为 closed。`lab.wait --controller-pid` 保留旧兼容模式，只提供 PID 存在提示，不能证明出生身份，也不授予清理或重试权限。

实际原件在 [readback.json](../../runs/experiment-operations/20261002/process-identity/readback.json)，旁边保留四份来源 JSON 字节副本与 SHA。独立系统命令只读取 `ps` 和 boot UUID；没有构造进程样本或运行测试。

| 真实来源 | 系统读回 | 修改后的判断 |
| --- | --- | --- |
| preservation/github/controller-active.json，PID 98966 | ps exit1，无输出；libproc ESRCH | lost |
| 首轮 experiment/active.json，PID 15711 | ps exit1，无输出；libproc ESRCH | lost |
| revision2/experiment/active.json，PID 93077 | ps exit0，2026-10-01 22:32:45 出生；libproc `1790865165.303439` | 旧空出生记录 unknown，不回填；当前出生读取为非空 |
| preservation/github/run.json，PID 98998 | ps exit1；原记录没有 host | unknown，缺宿主事实不能放行 |

本机 sysctl 独立读回 boot UUID `D62D2D5B-00BD-4D65-A4AF-A875E7C51279`，与 API 当前读取一致。五个相关模块 `py_compile` 成功，`git diff --check` 成功。没有编写或运行 Factory/Braid 测试、smoke、自检、探针，也没有对源记录执行 reconcile 或 cleanup。只读观察不能证明所有 PID 重用、权限错误或跨宿主边界已经实际发生；Linux 分支未在本次 Mac 现场实际执行。新 controller/worker 持久登记和真实启动的正向 alive 验收仍须来自下一次获授权实际运行，不能用本次读取现行 PID 替代。

更省代码的 Mac `ps lstart` 只能提供秒级出生时间；这里保留原生微秒身份，避免把同秒 PID 重用当作同一进程。不引入额外依赖或身份回填迁移。
