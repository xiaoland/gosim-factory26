# Cell：恢复 Pi 与 Braid 的责任边界

状态：用户已确认调整后的范围并授权继续实施（2026-09-23）。本页作为本次边界修复与实验推进依据。此前给Braid增加僵尸识别的方向撤回，process_terminal_fix已中断且未修改源码。

## 结果与边界

Braid管理Issue/PR、上下文、指派与自己的Pi连接/主进程。Pi及pi-subagents管理原生执行与内部子代理。Factory只装配能力和收集诊断。Braid不读取内部child PID、foreground/background、lease或停止receipt，也不以这些信息决定上下文重建。旧writer失效、新上下文、新assignee恰一次唤醒仍由现有Braid对象/调度状态保证。

## 具体删除与替代

| 面 | 删除 | 保留或替代 |
| --- | --- | --- |
| Braid config/local | RuntimeBinding.native_teardown、NativeTeardown、native_teardown_configured投影 | provider连接、native home与根会话身份 |
| Braid provider/factory | .factory teardown-request/receipt协议、child proof校验、原生子会话文件扫描 | PiSessions无条件登记自己创建的PiProvider；teardown只调用其正常close，不因删掉hook跳过关闭 |
| Braid provider/pi | owned_descendants、capture_native_descendants、子进程扫描/群组信号/kill-0终态循环、自定义native_command停止指令 | 关闭RPC stdin，让Pi走正常shutdown；等待本Adapter拥有的Pi主进程退出。主进程关闭失败仍报告provider失败，不宣称内部子代理已停止 |
| Factory profiles/materializer | native_teardown注入、自定义停止命令装配 | pi-subagents、角色/模型/skills配置；需要的原始诊断 |
| Factory lifecycle扩展 | stop/control RPC、fence、receipt与lease终态推理 | 将已有会话关系采集缩减为被动观察；不阻止tool，不停止child，不参与调度 |
| Factory/提交包沙箱 | scripts/linux_sandbox.py、factory/submission isolation_prefix和关联沙箱preflight、包内装配与资格断言 | 直接启动native程序；构建/官方运行环境照其原本用途使用，不额外嵌套沙箱 |
| Factory archive/资格脚本 | 以child停止证明/诊断完整度阻断应用交付；强制foreground/background reset串联作为bench前置 | 原始会话与可证明的父子关系、独立诊断状态；缺失标partial/unknown，不伪造完整成本或关联。应用本身仍须有效delivery commit与标准目录 |

Pi 0.85.1已安装实现可见：rpc-mode.js的stdin end调用shutdown，shutdown调用runtimeHost.dispose，后者发session_shutdown(reason=quit)。因此普通会话关闭已有入口，无须通过Factory扩展自造停止命令。这只证明入口存在，不证明pi-subagents所有内部资源均能正确清理；内部缺陷应在所属组件定向处理。

本轮SVC接线、模型配方与四variant实验仍在范围内；当前边界修复不额外更换已装配配方或扩大Corpus正文修改。用户明确要求不需要任何自建沙箱，包括本地开发环境：删除Linux Landlock、macOS sandbox-exec、Linux bwrap入口及沙箱资格关卡，不新增替代沙箱或配置开关。普通工作目录、会话配置、产物身份仍服务于运行和诊断，不施加文件访问限制。已通过的浏览器与包依赖检查按相关变化复用。旧ZIP保留为历史，移除binding字段后由新包消费新Braid，不混搭旧配置。

## 最快验收路径

1. 运行现有受影响的配置、writer fencing、指派/重建与归档检查；删除测试中对已撤回自有协议的要求。不新造Pi模拟器或三层测试框架。
2. 复用现有Linux运行环境，只替换本次构建的Braid与Factory材料，跑一次小型真实模型旅程：使用原生sub-agent完成局部工作，修改Issue description后接续上下文，通过PR交付可检查文件。以可见Issue/PR状态、旧writer拒绝、新会话和应用结果判断Braid；内部资源异常单列Pi/pi-subagents诊断，不再要求receipt。
3. 通过后构建一个候选，直接在官方Competition完成其Keep/BookStack。只做包身份/入口及本次变化涉及的检查，不重采既有模型与浏览器资格。
4. 首个官方候选闭环后展开其余既定variant；比较矩阵仍使用同一冻结Harness revision。如首候选发现设施缺陷，修复后统一revision，不混拼结果。取得既定实验结果后汇报，不自动开启下一轮。

模型额度不是本次验证路线的主要约束。优先比较取得有效证据所需墙钟时间，不以“无模型”作为方法优劣的替代指标。后台程序/运行owner收取终态，不由主会话反复poll。

## 实施顺序与分工

1. 开工确认后记录当前Factory与Braid基线，仅提交本任务材料；不包含tasks/competition-p0/packet.md。
2. 主Agent负责Braid字段/registry/正常Pi关闭，独立worker负责Factory装配与被动归档；双方共享接口是“取消native_teardown且主进程仍正常关闭；Factory直接启动程序而不附加沙箱前缀”，不同时改同文件。
3. 集成受影响的已有检查，直接进入一次真实Linux小旅程；失败按所属组件诊断，不扩展Braid内部子代理管理。
4. 复用runtime缓存打包首候选；运行owner持有官方执行/等待，主Agent处理终态决策。

主要影响：删除一个自有生命周期协议，改变Pi退出方式；原生子代理状态不再是Braid放行依据，诊断不完整不再伪装为应用生成失败。

独立只读预演已完成（pi_boundary_rehearsal，Luna medium）：已安装pi-subagents0.56.0在`src/extension/index.ts:1033`响应session_shutdown，cleanup主要处置watcher/poller/scheduler等运行时状态；`src/runs/background/async-job-tracker.ts:662`的dispose没有承诺终止全部后台child。foreground execution有AbortSignal→SIGTERM/SIGKILL映射，但shutdown到全部child abort的完整绑定未确证。该结果限制我们的声明：不能声称EOF证明所有子代理都停止，也不能因此恢复Braid的兜底协议。真实运行中若出现内部异常，按Pi/pi-subagents故障处理；此次预演不扩展成模拟系统。

## 当前验证

Braid实现已提交`fdb5c19`，删除580行、增加41行；29个单元检查与1个CLI检查通过。Factory删除自建沙箱与主动生命周期扩展，改用被动observer；`make test`的124个Python检查和Node observer检查通过，原始输出`/tmp/f26-boundary-full-tests.log`。Debian构建二进制已装入既有Linux容器的`/tmp/factory26-live/boundary-dev/runtime/bin/braid`，短真实运行已启动，终态owner为factory_boundary_cleanup，持久记录为容器`evidence/braid-boundary-process.json`，本机归档目标`runs/qualification/pi-boundary/live/`。正式候选`runs/packages/iteration-throughput/pi-team-mixed-boundary.zip`已通过载荷身份检查，SHA256为`c64ab94b7607aa8008a92dfac1794e5a602365ad3c5bd3b5a2ebe96e0617e0a7`；官网状态目录`runs/competition/iteration-throughput-boundary-20260923/hosted/pi-team-mixed`仅完成本地prepare，尚未上传或评分。

真实旅程于2026-09-23完成：Braid result为completed、根Issue已关闭、PR已MERGED，交付commit为`5c76438d864950a261d41663c714fc0f9491966d`。原资格脚本错把CLI状态和小写merged比较，导致退出1；已按真实接口修正，并对同一交付运行文件断言复验通过，没有重新采样。原始失败记录保留，纠正证据为`runs/qualification/pi-boundary/live/braid-boundary/recheck.json`。原生诊断partial（一个替换会话首行不是session header），不阻断有效交付。四包清单已冻结，官网controller已启动，先mixed两题，再deepseek、glm、vv；官网状态归属`runs/competition/iteration-throughput-boundary-20260923/`，尚无评分结果。
