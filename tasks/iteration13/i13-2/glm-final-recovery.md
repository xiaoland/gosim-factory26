# I13 GLM 两题恢复只读交接

2026-10-02，主线要求接续 GLM/GitHub 与 GLM/Sheet 后，用户最新要求先整理情况，并将开展实验基础设施重构。主线因此撤回本阶段新冻结、prepare、launch 和模型请求；当前只完成只读核对。

消费原交接 `runs/iteration13/i13-2-20261001/arc-hot-recovery-20261002/handoff-state.json`、两题保全 receipt/source-stop、Linux 修复 identity、恢复及本地实验文档。独立 Docker 盘点和输入 SHA 已保存到 `runs/iteration13/i13-2-20261001/glm-final-recovery-20261002/`。

没有创建包、operation、recipe 或离线准备，没有修改共享源码、原冻结输入、原 source/helper/volume；没有操作 SIGSTOP 进程、dispatcher、官网或 Flash/GitHub。没有模型请求、commit、push。

两题源容器已退出，当前独立读回保存具体 State。原 e209 修复二进制和 workspace ZIP SHA 已读回；全量 Git/DB/native 一致性仍依赖既有完整保全验证，本轮未再扫描全部原生历史。旧 source-stop JSON 的 `container` 是对象、状态位于 `readback.state`，而现 packager 期望标量 container_id 与 after/state；后续需要有出处的私有派生绑定，尚未创建。

准入原 registry 有三个 alive owner reservation；其中两个绑定当前 paused I14 容器，cleaner 的 reservation 对应已退出容器但 owner 仍存活。未释放或接管。按当次盘点，五槽最多还余两槽；这不是后续启动许可，后续必须重新核对实际容量、daemon/boot/UID/image、来源和唯一运行身份。

下一阶段由主线重新明确模型和供应商边界、范围及授权。本交接不自行改为 Qwen、不将 ARC 固定为新产品约定、不启动两题。
