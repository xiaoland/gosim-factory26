# 两次停滞的因果链与治理边界

## ST-1：把原生冷启动当成普通 RPC

第一轮 GitHub 可行性接续有四项新会话未取得 native identity，只留下 `session is unavailable`。
第二轮 GitHub/Sheet 的原始日志补齐后，五个当前失败项均指向本地 `Pi new_session RPC failed: provider request pi_rpc timed out`。
09-30 09:32 的 GitHub 再接续又以同样方式失败三项；这发生在模型请求之前，不是 GLM/DeepSeek API 慢，也不是需求推理困难。

实际冻结 Pi 0.85.1 的 `createSessionManager` 在没有 `--session` / `--continue` 时直接创建新会话。
Braid 却在 spawn 后立即发送 `new_session`，让 Pi 再执行旧 runtime teardown、services/extension reload、session rebind，然后才 `get_state`。
30 秒等待同时覆盖进程冷启动和这次多余的替换；这混淆了进程就绪和已就绪进程的控制请求。
独立抽取的实际 Pi 源码在 `runs/iteration11/runtime-stalls/pi-source/`，非用最新上游源码推断旧产物。

09:48 的 Sheet 同一旧 binary 成功恢复 root 与 PR13，并收到真实 GLM/DeepSeek 响应。
其 Pi 自带 main 初始化计时分别为14857/14875ms，extensions分项约14069/14002ms，分项包含于前者，不能相加。
这证明启动并非永久死锁，但不是对此前30秒具体内部耗时的完整重建。
旧失败没有逐阶段时间，不能断言“全部超时只由重复初始化造成”。

修复：新建进程只做一次 `get_state` 身份握手；恢复用原有 `--session`；冷启动有独立可调时限，普通控制请求保持原时限。
保留真实请求名、PID、cwd、native home、Pi startup timing，下一次若仍失败可直接区分进程加载与已启动 RPC。
失败不循环换会话或模型，不由 Braid 接管 Pi 子代理生命周期。

09-30 09:59 CST 的新 GitHub 实际接续补齐直接证据：PR22、root、Issue10 的首次握手分别122763、124012、129190ms，随后三者均产生真实模型响应。旧30秒时限会在这些正常启动完成前杀掉进程；独立冷启动时限与单次初始化已通过此次真实恢复。Pi main内部计时约29.8秒，但spawn到打印该计时约107秒，说明main前加载也耗时，不能仅凭extensions分项解释全部等待。恢复后root成功读取#331/#332，#332投递从queued变为delivered；不是仅解除blocked字段。

## ST-2：失败被永久锁住，恢复又依赖偶然的文案和字段形态

旧 transport 错误被映射为 unavailable，reset/agent/provider 随之 blocked。
第一版离线恢复限定 `active_turn_id IS NULL`，但 GitHub 三条 reset 指向的旧 turn 已 completed；保存历史关联并不意味着它仍在执行。
三条请求因这个偶然条件被漏选。
前一补丁已允许“引用确属旧 session 且已 completed”的 turn；09:32 三个新 physical 是它确实生效的证据，随后仍超时属于 ST-1。

本轮进一步去除固定字符串 `session is unavailable` 对恢复资格的影响。
资格以同一仍 OPEN 的责任关系、无后续成功会话、失败物化无 native identity、旧环境已停止及旧 turn 已完成等持久事实判断。
具体错误保留在物化/reset 记录中；不为恢复资格而丢失原错。

## ST-3：运行过程活着，被误当作工作仍在推进

GitHub 根在09-29 16:50Z之后没有 assistant，Sheet root/PR13从当次接续就没有取得原生身份。
其余成员完成已有工作后，两题均长时间0 running turn；容器和 Braid 的外层进程仍存活。
本次 launcher 只启动 lab run，未实际接续监控采样调用者。
旧的监控脚本存在于另一实验目录，并不意味着它监视 I11。

修复复用 `factory show` 的结果解释和新增 `factory watch` 调用同一解释。
呈现当前 OPEN 负责人阻塞和原始错误，排除已关闭历史错误；无活动且根被阻断时发出明确设施阻断信号。
watch 在前10分钟每3分钟、之后每8分钟采样，终态或明确阻断时退出交回，不自动重建、取消、评分或篡改 run 的原始生命周期。
新接续必须实际启动并保存该进程与输出，详见 [观测接线](observability.md)。

## ST-4：恢复本身不断复制大型现场

每次冷恢复重复打包、复制、解压6–8GB现场及运行时，引入大量磁盘 I/O 和空间放大。
09:41–09:55的宿主观测中 I/O pressure full avg60约39–45%，swap4GiB已满，磁盘从7.9GiB下降到1.7GiB。
这是当前明确的运行环境风险，不能倒推为昨日每次失败的唯一原因。

同一机器的恢复改用已有 `continue-in-place.py`：确认旧执行停止后保留当前完整工作区，记录旧二进制/DB/日志/refs，只替换必要 Braid 程序后 offline-resume。
全量归档仍用于保留原始证据与跨机器搬迁；不再为同机每次局部代码修复重复复制现场。
只清理本任务已归档、已不消费的可重建重复材料，I10原件、当前应用、Git及原生会话不动。
