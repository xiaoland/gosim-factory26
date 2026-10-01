# Console 讨论根操作入口

2026-09-30。属于 Console 实验设施接口适配，不属于 I13 Harness 迭代。依据 [packet](packet.md) 的授权“braid console的修改方案不需要我复核，可以直接应用”，源码修正及20:21 CST前端部署完成；未提交。

新 Braid CLI 的 C02 只接受讨论根 ID，见 [CLI 实施](../iteration13/cli-implementation.md)。原页面在每条评论卡片上提供 resolve/unresolve，并发送该条评论 ID，导致回复操作隐式扩大到整串；新 binary 将明确拒绝该调用。

本次只修改 `braid-console/web/src/Discussion.tsx`：整串解决和取消解决集中在每串的“讨论根 #ID”入口，直接发送 thread_root 对应的根 ID。入口独立于已解决历史的展开状态，因此历史折叠后仍可取消整串解决。按钮只在可写且存在未删除根评论时呈现，继续遵守忙碌状态。范围说明明确解决折叠整串已有评论、取消解决展开已解决历史，新回复不会自动折叠；评论卡片仅保留回复、隐藏此条和取消此条隐藏。

继续使用现有 Action 和服务端 CLI 桥，没有新增协议、兼容层或回复到根的服务端转换。当前旧 binary 与未来新 binary 均接受根 ID；这是调用契约适配结论，本次没有对任一运行中的 binary 执行写操作。没有修改 Braid、server 桥、I12 runtime、冻结材料、运行对象或恢复状态。

在现有 `braid-console/web` 工作目录执行 `pnpm run build`，退出 0；TypeScript `tsc -b` 与 Vite 构建均通过。构建产物为 `index-BQqj3ZLC.js` 和 `index-D_SK0Cwi.css`。Vite 仍提示既有主 bundle 超过 500 kB，本次没有新增依赖或扩展构建优化范围。

源码阶段未建立或运行测试、mock、probe，未跑模型、提交或操作真实评论。真实整串解决/取消解决、局部隐藏与新回复可见性尚未实测；编译和下述页面读取不能代替实际写入验收。

## 接续后的部署与页面核对

20:21 CST沿既有Console授权部署已构建的 `index-BQqj3ZLC.js` 和index.html到WSL原dist。先复制旧index到证据目录，再新增资源并原子替换index；保留旧资源，Console PID 204242及backend、registry、journal、I12 binary均不变，无需重启服务。此前WSL只部署backend和dist，没有前端src目录，本次继续部署产物，不为接续增加构建环境。

实际HTTP读取index/JS/CSS均为200，返回hash与Mac产物相同。GitHub根Issue页面已显示“讨论根 #ID”“解决整串讨论/取消整串解决”，历史折叠时仍有根操作；评论卡片只显示回复和“隐藏此条”。范围说明明确已有前缀、新回复与局部隐藏。实际控制状态同时显示GitHub运行中、Sheet暂停；临时后台核验页面已关闭，没有操作用户原页面或业务按钮。

部署前后运行PID、StartedAt和暂停状态一致；本次不执行pause/resume、编辑、评论或resolve。原journal的19:25:33 CST记录表明GitHub此前已经通过Console恢复，该事实更正了旧packet中“两题均暂停”的当前状态，不是本次部署造成的恢复。

前后回执最初写到WSL `runs/braid-console-control/20260930-cli-root-actions/{before.json,deployment.json,index.before.html}`。20:29 CST复制时返回ENOENT，随后核对整个 `runs/braid-console-control/` 不可见；原因未定，旧index备份现在不能确认仍存在。本会话按已返回的实际工具回包保存 `before.from-tool.json`、`deployment.from-tool.json`，另保存实际浏览器观察与从原journal读取的控制记录，统一在Mac `runs/iteration13/thread-handoff-20260930/console/`；`evidence-provenance.json`明确这不是远端文件复制成功。再次实际读取远端产物及Mac转发HTTP，hash仍一致。JS SHA-256为 `71c4f4bf1a348d57674788671224634f15b9c3ab40e4b9507b2d56c7197be296`；index为 `2cf3b86ef1944034e9232e6eb137a3f55483b69daf315cb85b8062f550bff43f`。没有新测试或新模型运行。
