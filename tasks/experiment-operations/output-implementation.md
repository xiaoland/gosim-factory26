# 执行输出保全的实施证据

2026-10-02，执行输出使用独立 `workspace-output-sha256-v1` 清单，保留普通文件内容、执行位、目录与符号链接字面值。输出可能包含执行容器绝对链接或原本悬空的外链；清单不跟随链接，不从宿主读取目标。严格输入冻结算法保持不变。解包先验证所有成员路径及父节点类型，再写普通数据，最后创建符号链接；不能经归档链接写出目标目录。

`docker_workspace.Workspace.recover` 保存原始 tar、远端输出清单、原始错误和后续错误列表。停止执行后由 runner 拥有自动回收，正常和 finally 路径最多尝试一次；adapter 的 finally 只核对已有 verified 输出，不再对 pending 或 failed 状态补做自动回收。显式 cleanup 保留补采能力。核验失败保留卷和 helper，不删除远端唯一副本。生成容器退出码与输出回收失败并列保留，adapter 报 output-recovery 阶段，不将设施错误泛化为模型未交付。

两份真实 Docker cp 原始 tar 在新私有目录通过生产解包函数处理。Sheet 68057 项、GitHub 77898 项与当时的 remote-after-manifest.json 完整 entries 相同。证据是 `runs/experiment-operations/20261002/output-recovery/{sheet,github}/frozen-source-readback.json`；包括全部链接字面值，不只两条已知错误路径。没有修改原 tar、失败卷或活动执行。

最初将新的解包与历史已解包目录比较发现 Sheet 五项差异，已保留 `source-tree-differences.json` 和首轮失败回执：后续 SQLite/Git 取证在旧目录留下新 WAL/SHM/错误 URI 文件并刷新两个 Git index。这些变化不存在于原始 tar 和当时冻结清单。验收因此使用原始远端冻结清单作依据，而非将后来可变目录当作同一恢复时点；最终两份 tar 均完全匹配。此反馈证明已有真实链接可保全，不等于新收费执行的远程中断/再次显式补采已经实测。
