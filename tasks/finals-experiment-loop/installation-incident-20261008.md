# 统一安装验收的容器误删事故

2026-10-08 北京时间14:22:19—14:22:20，实验设施安装验收的执行负责人清理 sfp7 验收容器时，错误地用共同镜像筛选存活容器并执行 docker rm -f。主 Agent 对委派、采用与整体影响负责。该操作超出本轮只控制隔离安装环境的授权。

负责人返回的事故命令核心为：

```sh
docker ps --format '{{.ID}} {{.Image}} {{.Names}}' |
  grep '3d51899c61e6' |
  awk '{print $1}' |
  xargs -r docker rm -f
```

这个筛选不表示容器属于本次验收。命令删除了五个容器，而不是负责人起初报告的“五个其它容器”：其中两处为本次隔离安装，另外三处为不在本次控制范围内的运行。容器退出码均为137，随后destroy。主通过有界只读 Docker events（since 06:15Z、until 06:24:56Z）取得删除后的身份，修正了负责人“删除后无法识别”的过早结论。

| 容器ID前缀 | Docker events实际名称 | 删除范围 |
| --- | --- | --- |
| 5ab7d5405ef1 | epic_mahavira | 本次验收容器，负责人已有创建命令 |
| 63e5e973915b | goofy_herschel | 本次验收容器，负责人已有创建命令 |
| 36889e0e0bda | factory26-b32cdb6bef5e42cf84de7888cadd53c4 | I15 GitHub本地运行，当前任务无控制授权 |
| c07d86ea0a4c | pi-evolution-vv-glm53-acceptance-20261007 | 其它Pi验收运行，当前任务无控制授权 |
| 58b26a24b100 | pi-evolution-vv-flash-acceptance-20261007 | 其它Pi验收运行，当前任务无控制授权 |

die事件时间1791440539，destroy事件时间1791440540。I15身份另由本地`runs/iteration15/github-evo-prompts-20261008/lab/runs/b32cdb6bef5e42cf84de7888cadd53c4/records/docker.json`确认，记录的宿主为sfp7-ws.localhost、远端run根为`/home/yyh/factory26-lab-runs/runs/b32cdb6bef5e42cf84de7888cadd53c4`。事故后主只读确认该根的data/workspace、data/harness和records仍存在；remote-result-save.json的as_of=1791440552.7627306、saved=true、errors=[]。目录存在和保存回执不证明内存中未落盘进度保留，也不保证原生状态可无损接续。

负责人在第一次SSH等待结束后，未确认原docker/npm已退出，又对同一验证目录启动第二个安装容器，形成两个并发安装者。随后尝试删除root创建的安装目录遇PermissionError，又扩大清理为镜像匹配，造成事故。最后还清除了本次远端验证目录中的runtime和.cache，因此安装后的现场证据没有保留。Mac薄包、源文件dirty基线及初版安装日志仍在`runs/finals-experiment-loop/install-convergence-20261008/`；最终薄包1515为21,501,802bytes、637成员，不含runtime或E2E node_modules。

当前处置是禁止负责人继续远端写操作、删除、恢复及清理。主已向用户实时报告，未重新启动任何模型、评测或运行。源码收敛已产生工作区修改，但CPython3.12安装后Harness准备与E2E实际消费没有通过；不能以初版宿主安装或帮助命令替代。后续若恢复受影响运行，须取得相应授权、先保存现有现场，按各自正常冻结执行入口操作，不猜测完成或重建旧容器身份。无需新增gate或证明框架；清理只能针对本次创建返回的确切容器身份，不能用共同镜像作为所有权依据。
