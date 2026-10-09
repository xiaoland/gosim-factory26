# 停止、重跑与接续

Lab 的 `restart` 默认从题目基线重跑；显式 `--keep-data` 才迁移应用和原生状态。这两个操作都会创建新 run，来源现场保留。完整接口和适用边界见 [Lab](../../lab/README.md)。

## 当前 run 的停止与接续

```sh
python3 -m lab status RUN --json
python3 -m lab stop RUN
python3 -m lab restart RUN
python3 -m lab restart RUN --keep-data
python3 -m lab restart RUN --keep-data --task NEXT_TASK
```

`stop` 的停止回执、data 保存和日志回收分别核对。接续必须使用同一 variant：同 task 和需求版本恢复原生状态，新 task 保留应用与历史并创建新的原生任务状态。旧 records、费用和隐藏评分不迁入新 run。来源缺失时报告可继续的范围，不能静默转成空工作区。

接续重新装配程序，并按 target 名称解析当前配置；来源停止和保存使用来源的冻结配置。需要固定旧 runtime 时使用明确的 `LAB_CONFIG`。应用或 Git 备份不等于完整检查点，重新装配程序也不表示恢复了完全相同的执行环境。

Local I15 在同任务、同原生 scope、同执行宿主和远端目录且未指定 snapshot 时，可以在来源停止并取得完整保存回执后独立复制远端 data。远端保存回执不证明 Mac 已回收完整 data；跨宿主、不同任务或 snapshot 仍按完整回收与迁移流程处理。具体实现和路由变更限制见 [Lab](../../lab/README.md)。

自管 Docker 的 pause/resume 保持同一次执行，不保证释放资源或保住外部连接；Hosted 不支持。疑似停滞先读回事实，再按实际执行器能力控制。平台 `can_resume` 字段本身不证明原生进度可恢复。

## 独立应用评测

Pi 的最终模型错误不会自动停止已启动的后台作业。原生归档中的终态后台工作记录与结果文件仍需读取；作业引用不等于成功的检查点。供应商响应头超时也不能证明请求未执行或未计费，不能据此自动跨供应商重放。

已有应用可以冻结后独立评价，不必恢复生成。使用 `python3 -m lab evaluate RUN --kind KIND`，支持的 kind、配置与快照边界见 [ARC 适配](../../lab/arc_bench/README.md)。阶段应用必须绑定明确 commit；生成耗时、评分耗时与费用分别记录，隐藏反馈不进入仍在生成的 Agent。

## 历史恢复

当前 CLI 没有 checkpoint、recover 或 prepare 命令。旧 schema3/4 的 checkpoint、prepared 和 writer 合同只由[历史执行器](../../lab/exp/README.md)解释，入口见[历史恢复](history/recovery.md)。旧材料不能因新版源码存在而自动升级为完整检查点。
