# 实施与反馈

源码在 feat/experiment-startup-dx 隔离分支实现，未修改主工作区或接管实验。`local_job` 是公共 ARC job 构造与输入角色解释边界，arc_matrix 与 intent compiler 共用；低层 recipe 仍为 local + external_docker。

高层 generate 使用 `operation: arc-local-generate`、`purpose: generate`、agent/requirements inputs 和 limits；case.backend 只选择 competition_id/task，环境 `arc` 使用 sdk_source 与 target（完整 endpoint、immutable image_id、slots、admission_volume、authority_handoff，可选 python）。command/backend 由设施生成，拒绝模板手工重复权威。Python 用 `{runtime_python}` 由实际 runner deployment 解析，不与 runner SDK input 同名。native 模型 bindings 由 models 冻结。

build 在实际绑定后读取宿主 SDK main/run_container 与来源SHA、Linux/amd64 Node/Braid ELF头及公开需求；目录材料消费真实已发布artifact的producer provenance，ZIP才读取package-manifest。不向不可变目录补manifest。未生产 from_production 在compile保持关系，在doctor显示等待；不为compile安装runtime或提前生产材料。admission与doctor共用协议2卷身份解释，保留真实旧卷拒绝和handoff边界。

adapter在单一环境文件生产处合并编译公开模型政策、选定凭据变量，冲突只报告key；SDK子容器创建后、启动前按真实Config.Env读回，回执只保留变量名、公开政策hash及container identity。新contract的wrapper从设施冻结ResourceEvidence实现在实际子namespace取得cgroup并持续采样，发布本namespace services；bootstrap及已启动collector归同一try/finally。旧无contract入口保留process.wait，不强制其提供新的Factory support。未执行子容器，以上是已实现合同而非已观察运行结果。

实际反馈入口：

- actual-material-readback.json：现存I14 Linux ZIP、实际宿主SDK与公开GitHub需求的离线角色读回。
- actual-directory-readback.json：真实material-591f24ea目录和producer原receipt读回，该目录无package-manifest，未补写或修改原材料。
- actual-plan-readback.json：由实际I14输入/模型/目标身份派生的完整compile成功，from_production保留；宿主runtime与材料均build-required，未创建producer cache。首次失败的endpoint可选environment字段假设已修，原错保留在runs/experiment-startup-dx/offline-plan/compiled。
- example-intent.json 与 example-environment.json：本次真实公开计划的可复用输入示例；authorization明确仅离线用途，不构成模型/Docker启动许可。
- source-readback.json：10个当前源码及两个生成wrapper的内存compile身份。有限git diff --check通过。

没有运行SDK、Docker、模型、平台、测试/模拟/探针/smoke，没有生产或复制大材料。没有测量实际启动耗时，没有取得子容器真实环境、ResourceEvidence或模型首次活动验收；这些需要另行已授权运行。主区并行修复重叠仅精确采用adapter的read_json与runner的platform import；不复制agent_support的variant内部单次bootstrap或其它在途改动。
