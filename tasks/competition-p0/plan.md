# 参赛包实施方案

## 运行边界

由独立 main.py 包装接收外部需求与输出路径，读取平台 OPENAI_API_KEY、OPENAI_BASE_URL、MODEL（视觉配置按已核实平台协议处理）。平台模式不读取用户本机密钥、不取固定 benchmark、不运行评测。保持一个 backend 一种包，默认 Pi，兼容 Codex + LiteLLM。已有 factory.generate 接受显式需求与打包运行环境，保留原有本地调用。

源码/依赖在打包时固定：Braid 使用 Linux x86_64 构建，SVC 用包含 Corpus 的 wheel，Pi/Codex 使用固定 npm 版本，Codex 适配器固定版本。构建时可以访问依赖源，比赛运行无需 GitHub clone、Cargo 或复制宿主 venv。参赛包只列入必要文件并记录哈希。平台容器不假定 bwrap 可用；使用独立单线程 Linux Landlock launcher（ABI >= 3）设置 no_new_privs 后 exec，任何不支持或被 seccomp 拒绝均失败关闭。需求放在可写 work 的外部 sibling，避免父目录授权覆盖只读规则。只授权必要系统目录与运行制品，不授权 /workspace、/tmp、/proc 整体；网络白名单仍由平台负责。采用权限隔离，拒绝读取 /workspace/tests，需求只读，主进程保留原生证据读取能力。

正式交付必须含 frontend/package.json（build）和 backend/package.json（start），backend 通过 HOST/PORT 提供前端产物及 API。不依赖本地专用 deploy.sh。平台输出可能已有 requirements 和 .arc，不能清空输出目录或覆盖平台元数据。现有本地应用契约以归档配置区分，历史结果不改写。

Playground 保留练习能力，入口明确其不计正式成绩；不得猜测正式 API。若正式 API 无公开证据，则参赛包通过队长的正式平台入口使用，不新增猜测接口。

## 实施与验收顺序

1. 核对官方源码、独立 advisor 复核运行边界和验收方案，独立 Agent 预演实施步骤；将通过的决定记录在 packet 并提交。
2. 修改共享生成边界并新增参赛入口、Linux 打包与包清单。验证输入/输出路径、安全失败、凭据优先级、布局、失败退出和交付冻结。最小扩展，不重写调度器。
3. 在可用 Linux 容器构建并运行真实工具版本/Corpus 无模型检查；用测试专用替身驱动入口，验证成功/失败、隔离及部署。不启动模型或平台评测。
4. 完成 make test、文档链接、SVC status、独立代码与证据复核；更新长期文档、汇报明确限制并提交本任务变更。按仓库约定，完成时整合长期事实后删除任务包；若验收受阻则保留。

## 复核结论

advisor 已复核运行边界与验收：支持单独 Landlock launcher，不做 root chmod 或无隔离回退；必须用存在且父进程可读的标记测试子孙继承、读取拒绝和需求写/截断/替换拒绝。公开模拟环境默认非 root，生产 Runner/镜像不随仓库提供；精确线上兼容性不由本地推导。

已验证原生 x86_64 Docker context `arcbox-win` 支持 Landlock ABI 7。Pi 0.85.1 的 npm 包为 @earendil-works/pi-coding-agent，要求 Node >=22.19，包内携带 Node 22.22.3；Python 依赖用 Linux CPython 3.12 的 pip --target 安装，不复制 venv。包内 runtime/bin、runtime/node_modules、runtime/python 提供工具，manifest 记录全部载荷 SHA256 与源码身份。完整 VISUAL 配置优先，否则使用 OPENAI 三元组；不存在本机密钥回退。

活动配置采用 deployment=arcbench，生成提示与本地部署检查一同切换为 frontend/backend；旧 run 缺少该字段时继续使用原根 package.json 契约。正式输出只交付验证过的冻结文件，保留平台 requirements/.arc/.git，并拒绝应用写入这些保留路径。官方镜像缺失时不虚构验收：使用已验证 Landlock ABI7 的原生 x86_64 Docker context arcbox-win 完成独立容器证明。
