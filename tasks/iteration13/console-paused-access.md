# Console 暂停后访问

2026-09-30。已部署，真实CLI、HTTP与浏览器读取完成。支线范围：修复I12已暂停运行的人工查看与介入接线，不恢复生成、不实现暂停/恢复按钮、不改变Braid或生成应用。
用户已明确要求修复暂停后仍可查看和人工介入；主线据此授权诊断、实现和部署到现有Console，提交由主线统一处理。

## 表现与根因

现有HTTP `GET /api/items?run=i12-restart-github` 实际返回400，原错误为 `CLI 退出码 1: Error response from daemon: Container f26-restart-4ad2b95fc11c89 is paused, unpause the container before exec`。
两题registry通过`docker exec -i`在原生成容器执行CLI；Docker整体暂停冻结全部生成进程，也拒绝新增exec。HTTP错误源于该生命周期耦合，不能通过吞掉错误或返回空列表处理。

GitHub原容器为`8c0f26c7ed6d49de3fb36ac63ca74d9c4bad6e783a35a151480bafbddc8ac0a1`，Braid run为`20260930-071413-6b4bf7a8`；Sheet原容器为`03e4add757602bce17b57ff10851639583f565cd2745b989cb5fc1a09c129a6f`，Braid run为`20260930-071413-6fe73efc`。实际核对均Running=true、Paused=true，PID分别5217和5181。
两容器固定image为`sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`，用户为`1000:1000`，工作目录为`/workspace`；各题`official-generation`读写挂载到`/workspace`，本轮`shared-submission`只读挂载到`/workspace/submission`。state、Git和binary均在这两处挂载中，数据库中的绝对路径使用该容器路径空间。

## 实现与边界

复用现有registry的`cli_command`，为每run创建一个同image的独立CLI访问容器，`--network none --volumes-from <原容器完整ID>`沿用原用户及工作目录，覆盖entrypoint为`sleep infinity`。Console通过`docker exec -i <访问容器完整ID> env -u … <原binary> --state <原state>`清理三项`BRAID_*`身份变量并执行同一对象CLI。服务及前端无需新分支，也不新增接线生成器或第二套数据库接口。
独立访问容器共享原现场及挂载权限，生命周期不受原容器pause限制，没有继承原运行的凭据环境，不设自动重启。除了sleep待命，只执行请求的Issue/PR/comment对象命令，不启动`braid local`、worker或定期检查。容器启动、停止或移除均由操作方明确执行，缺失时不自动重建或回退。原生成容器保持暂停，恢复仍需用户明确指令。

Braid普通对象CLI直接使用`LocalObjects`访问现存SQLite；只有`local`命令启动runtime并获取`runtime.lock`。人工修改使用原事务并入队事件，CLI本身不运行模型。SQLite写锁属于实际进程与事务：暂停时若恰有写事务，独立容器不能让其释放。现有CLI的busy timeout和HTTP“不确定结果”journal语义保留；不解锁、不删除WAL/SHM、不切换状态副本、不自动重试。
独立advisor复核推荐本次只改registry和操作文档；实际HTTP反馈改变实现选择后再次复核，确认常驻访问容器消除创建开销且不需要Console状态机。读取验收不能证明可写，实际业务写入须凭真实CLI回执及读回结果记录。未向生成对象添加测试评论，也不执行Factory/Braid设施测试、自检或smoke。

## 实际操作证据

部署前直接使用独立CLI读取两题的Issue列表、PR列表和根Issue，六次命令均exit=0且stderr为空。GitHub为9个Issue、1个PR，根Issue revision=3、6条评论；Sheet为6个Issue、2个PR，根Issue revision=5、2条评论。命令包括容器完整身份及原始输出，保存在WSL `runs/iteration13/console-paused-access-20260930/cli-read-before-deploy.json`。
上述命令结束后，两原生成容器仍Running=true、Paused=true，PID保持5217/5181。image自身没有`BRAID_*`环境变量；正式registry仍显式清理身份变量。登记的宿主binary与挂载binary实际SHA256一致，均为`38c68450fa93399e7dabd3c4c912410a503e59152cb13f3d3c724ce7d9fc708d`。

第一次配置让每次请求都创建一次性CLI容器。独立单条读取耗时4.15–5.62秒，但真实HTTP及已有页面的5秒轮询下，多个请求超过30秒；Docker实际出现多个`Created`容器，部分尚未启动CLI，`docker ps`也变慢。因此失败发生在容器创建/启动路径，单条CLI成功不能代表稳定HTTP交互。原始HTTP错误保存在本地`http-read-after-deploy.json`，旧服务日志在WSL`console-server.log`；本轮仅中止新建容器的Console及其CLI客户端，按完整ID、创建时间、命令与原挂载身份确认并移除两条本支线遗留CLI容器，没有清理原生成。回执为`once-per-request-stop.json`及`once-per-request-orphan-containers.json`。

改为常驻访问容器后，同样的真实CLI读取耗时0.23–0.64秒，Issue列表和已有PR详情均exit=0。新Console PID为111070，仍监听WSL `127.0.0.1:8765`；registry为本轮原`console-runs.json`，journal仍为原`console-actions.jsonl`。访问容器名为`f26-console-i12-restart-github`和`f26-console-i12-restart-sheet`，完整身份、命令、image、mount、network与restart policy在WSL`persistent-access-deployment.json`；旧registry、新registry和服务回执分别保存在同目录，不改run ID。

Mac经既有8765转发实际读取`/api/runs`及两run的列表、根Issue、已有PR详情，七条请求全部HTTP200。对象请求耗时0.15–0.90秒：GitHub列表10项（9个Issue、1个PR），根Issue revision=3/6条评论，PR #2 revision=1/0条评论；Sheet列表8项（6个Issue、2个PR），根Issue revision=5/2条评论，PR #8 revision=1/4条评论。原始响应为本地`runs/iteration13/console-paused-access-20260930/http-read-persistent.json`。

浏览器实际看到GitHub的10项列表、根Issue完整正文、6条讨论及编辑/评论/回复入口，原超时错误已清除；切换Sheet后看到8项列表、根Issue完整正文、2条讨论及相同人工入口，没有HTTP错误。临时核验tab已关闭，未关闭用户原页面。没有为验证写入而发POST。人工写入接线已采用同一CLI容器，但此次真实业务写入未实测；暂停期间可能持有SQLite写锁的边界仍保留。暂停/恢复按钮及其产品控制能力由I13后续单元设计。

16:55 CST最终实际核对：原GitHub/Sheet容器仍Running=true、Paused=true、OOMKilled=false，原PID保持5217/5181；两个访问容器均Running=true、Paused=false、network=none、restart policy=no，`docker top`各只有一个`sleep`，没有Braid runtime或模型进程。完整回执为`final-container-states.json`。访问容器ID分别为`0559fdcab59ed010c05a530ecddc9549f5bd368b083ed03f7b578807e06a6535`及`a9994f3ae27a0e3d232a4d8c82e4db0d9480d354701206dbe1f799a93fcc9031`。

证据目录在Mac和WSL同相对路径`runs/iteration13/console-paused-access-20260930/`，运行材料不提交。长期操作知识更新到Braid Console README及部署说明；未修改server、前端、Braid、variant或生成应用源码，未提交。此支线已交回主线整合，下一次真实人工输入的可写回执及恢复操作归操作者的明确指令。
