# Console 服务与运行接入

本页维护当前服务准备、登记和解除接入方法。组件源码与前端构建从 [Console 入口](../../braid-console/README.md)定位；页面、对象、会话和代码读取行为统一见 [界面与读取合同](../../braid-console/docs/contracts.md)。旧暂停机制、部署 PID 与当时验收保存在 [Console 历史记录](history/console.md)，不能据此判断现在的服务身份或控制能力。

Console 只接入 Braid，不启动实验或代替 Lab 的状态与恢复入口。当前新接入拒绝暂停生成；恢复请求经过对应实验的冻结执行器，不绕过其能力门控。停止 HTTP、访问容器和生成执行是不同操作。

## 准备与启动服务

先按 [前端开发说明](../../braid-console/web/README.md)构建 `web/dist/`。选择现存、稳定的 Python 3.11 或更新解释器；解释器及其 prefix 不能位于 `runs/`、`prepared/` 或 `.factory26/`。服务必须准备在新目录，不能覆盖现有根；Mac 长期服务位于 WorkSSD，且在实验目录之外。下例中的 registry 是事先保存的 JSON 运行列表，可先写 `[]` 再登记实际接入。

```sh
console_service=/Volumes/WorkSSD/Services/factory26/exp-console/deployment-YYYYMMDD
console_registry=/Volumes/WorkSSD/Development/factory26/runs/console-input.json
console_python="<稳定 Python 的绝对路径>"
python3 braid-console/service.py prepare --destination "$console_service" \
  --registry "$console_registry" --python "$console_python"
python3 "$console_service/app/service.py" show --service "$console_service"
python3 "$console_service/app/service.py" serve --service "$console_service" --port 8765
```

`prepare` 冻结 Python 身份、应用源码、已构建前端及文件哈希，不复制实验工作区。`serve` 使用登记的解释器执行冻结 `app/server.py`，监听本机 `127.0.0.1`；不能从工作树直接启动 `server.py`。修改代码后准备另一新根，不编辑已冻结的 `app/`。独立开发制品可放 WorkSSD 的 `runs/` 并显式加 `--development-output`，它不是长期部署或已有服务迁移。

服务只接受 `factory26.exp-console-service` schema 1 manifest，不支持旧 registry/journal 启动参数或自由 `cli_command`。服务根的 `app/` 保存程序，`manifest.json` 保存制品与接入身份，`active.json` 保存 HTTP 实例，`logs/http.log` 每份最多 5MiB 并保留三份备份。`console-actions.jsonl` 保存人工与管理操作的 started/completed/unconfirmed 等回执，追加后 flush/fsync，不随访问日志轮转。HTTP 锁禁止同时启动第二实例或修改配置。

远端服务在执行宿主重新准备；WSL/sfp7 可使用核实后的远端存储，Mac 的控制记录与回收证据仍放 WorkSSD。远端浏览由操作方独立转发，例如 `ssh -N -L 8765:127.0.0.1:8765 wsl.win-ws.localhost`。转发进程不证明服务或生成执行已启动，服务也不管理转发。

## 选择读取来源与登记

每项使用唯一 `id` 和明确的 `mode`。从生产者发布的有效绑定选择实际运行；数据库出现后才登记，不能为页面预建数据库或把旧 state 改名冒充新执行。新增列表使用冻结管理程序登记，HTTP 须先停止：

```sh
python3 "$console_service/app/service.py" register --service "$console_service" \
  --registry /Volumes/WorkSSD/Development/factory26/runs/console-additions.json
python3 "$console_service/app/service.py" serve --service "$console_service" --port 8765
```

`register` 只追加，不替换现有列表。已使用或释放的 ID 都不能再次指向另一现场或归档；终态材料用新的 archive ID。`writable` 只表达对象修改许可，不授予生成控制或模型运行授权。

| 实际材料 | 接入方式 |
| --- | --- |
| 已保全的冻结对象与原文 | `archive`，只读，不需要原容器或 CLI。 |
| 本机原执行路径空间仍可达 | `live` 与受管理 Braid binary。 |
| 生成数据在容器 overlay 中 | `live` 的 `runtime-readonly`，读取原生成容器。 |
| 共享挂载且已有域管理访问容器 | `live` 的独立 accessor；须满足下节的域身份。 |

归档列表的最小示例：

```json
[
  {"id":"saved-run","label":"保存状态","mode":"archive","writable":false,
   "archive":"/Volumes/WorkSSD/Development/factory26/runs/saved-run/evidence"}
]
```

归档须有 `braid-state/braid.sqlite3`；以 `mode=ro&immutable=1` 读取，非空 WAL 明确拒绝，由生产者先保存完整冻结数据库。Console 不修复或合并归档，也不重新计算 Git、合并条件或调度事实。保存范围、旧 schema 缺口及 native manifest 的定位规则见读取合同。

同宿主现场的最小示例：

```json
[
  {"id":"local-live","label":"本机现场","mode":"live","writable":false,
   "state":"/Volumes/WorkSSD/Development/factory26/runs/execution/braid-state",
   "workspace":"/Volumes/WorkSSD/Development/factory26/runs/execution/workspace",
   "binary":"/Volumes/WorkSSD/Development/factory26/runs/execution/bin/braid"}
]
```

将路径替换为原执行空间的实际绝对路径。`binary` 会复制到服务的 `binaries/<sha256>/braid` 并核对身份；state 必须已有数据库，workspace 必须保留 Braid 保存的 Git 与工作树路径。可选 `run_record` 指定现存生产者 JSON，缺失时页面保持未知，不猜目录或实验名。

## 原生成容器的只读接入

生成数据位于 overlay、没有共享访问容器时，在持有原 experiment 与冻结 controller launcher 的宿主准备服务，并登记 `access_mode: "runtime-readonly"`。下例字段均须从实际身份与冻结执行回执取得；两个容器 ID 必须相同，顶层 state/workspace 是原容器路径，不伪装成宿主挂载。

```json
{
  "id":"running-readonly","label":"生成现场只读","mode":"live","writable":false,
  "state":"/workspace/actual/braid-state","workspace":"/workspace/actual",
  "binary":"/absolute/verified/same-byte/braid",
  "docker":{
    "access_mode":"runtime-readonly",
    "runtime_container":"<原容器完整64位ID>","cli_container":"<同一完整ID>",
    "endpoint":"ssh://<实际Docker宿主>","daemon_id":"<实际daemon ID>",
    "started_at":"<原StartedAt>","labels":{"<owner标签>":"<实际值>"},
    "binary":"/workspace/actual/bin/braid","binary_sha256":"<实际SHA-256>",
    "state":"/workspace/actual/braid-state","workspace":"/workspace/actual",
    "exp":{"experiment":"/absolute/frozen/experiment","attempt_id":"<实际attempt>"}
  }
}
```

把此对象放入登记列表。顶层 binary 仍是准备时可核对的同字节可执行制品；不声明 mounts、access_owner 或 access_resource_id。准备时冻结 controller 核对实际资源、出生身份、endpoint 与 daemon；读取再次核对容器、状态、数据库及 binary。容器须运行且未暂停。

此接入强制只读，禁止对象写入、暂停/恢复和 `access-start/access-stop`；`release` 只移除登记，不操作原生成容器。首页读取对应 attempt 的 `observation.json`，身份核对与原文尚未持久化的显示边界见 [读取合同](../../braid-console/docs/contracts.md#会话与原生正文)。未登记现场不会自动发现，容器结束后须保全材料并用新 ID 登记归档，不能改指另一次生成。

## 域管理的独立访问容器

新共享挂载接入要求访问容器已经属于原 attempt 的 Docker 管理域：资源 `role=accessor`、`workspace=attempt_id`，`access_resource_id` 对应该容器的物理出生身份，运行时拥有 workspace writer 覆盖。当前 `service.py` 没有创建此资源的命令；没有合法 accessor 时，应使用只读原容器或归档方式，不能沿用历史手工 `docker run` 绕过资源域。

先准备空服务取得 service ID，用下面命令取得受管理 binary 的实际路径，再核实已有访问资源挂载的是该文件：

```sh
python3 "$console_service/app/service.py" binary --service "$console_service" \
  --source /absolute/frozen/braid
```

在 live 登记中增加以下 docker 对象。生成与访问容器必须分离；顶层 state/workspace 是实际宿主映射，mounts 明确包含 workspace 根，state 按最长挂载映射须与顶层 state 相同。

```json
"docker": {
  "runtime_container":"<生成容器完整64位ID>",
  "cli_container":"<域管理访问容器完整64位ID>",
  "access_resource_id":"<已创建的accessor资源ID>",
  "context":"<同宿主Unix socket context>","binary":"/console/braid",
  "mounts":[{"source":"/absolute/original/workspace","destination":"/workspace"}],
  "state":"/workspace/actual/braid-state",
  "exp":{"experiment":"/absolute/frozen/experiment","attempt_id":"<实际attempt>"}
}
```

登记程序追加受管理 binary 的精确挂载，并要求访问容器带 `factory26.console.service=<服务ID>`、`factory26.console.run=<运行ID>` 所有权标签。实际镜像、用户、工作目录、原绝对路径与所有嵌套挂载须符合原运行。共享路径方式仅支持可核实的同宿主 Unix socket context；SSH 只读方式不能被当作跨宿主可写聚合。

## 会话原文与受管状态

当前 live provider 若为 `idle`、CLI 明确返回空 `turns`、读取从偏移零开始且该服务此前未读到该 provider 正文，精确登记的 JSONL 路径尚不存在时，原文接口返回 `availability: "not-persisted"`，页面显示文件目前不存在、等待首次轮次持久化对话。它不表示模型正在执行或已经交付应用；上下文替换后准备好但尚未收到新输入的 provider 可以处于这个状态。已有 Turn、该服务此前读到过正文、其它文件错误或非零偏移的缺失仍保留具体读取错误，不能都当作等待。


受管 state 的访问与恢复交接使用原 workspace 权威。Managed Docker Console 在每次 CLI 调用前查询同一 holder；capture 关闭旧访问写者后，旧 live 接入只能返回封口 snapshot 关系，不能继续读取新 writer 改写的工作区。快照需按实际资产位置取得并独立登记为 archive，live 配置不自动改绑到新 attempt。

新受管 Local state 尚无 Console 写者适配器。其 harness-layout 显式记录 state_holder，Console 对这类目录拒绝 live 接入，保留 archive 阅读；缺少该关系的历史材料沿原合同，不能据此声称已纳入受管关闭。运行域之外自行编辑目录同样不在登记覆盖内。

named volume 使用 `volume-subpath` 时，宿主 source 是 volume 根加实际 Subpath，不能仅用 volume 根或假定 `--volumes-from` 保留子目录。保持原 volume 与子目录的实际消费者引用；宿主目录供依赖保护，存在性在固定访问容器内核实。访问容器只提供 CLI 执行空间，不运行 Agent 或重建生成执行。

## 停止、解除与服务切换

使用对应终端 Ctrl-C，或向已核实的 HTTP PID 发送 SIGTERM，仅停止 HTTP；查看 `active.json` 的终态。管理命令与冻结服务配套，配置变更、访问容器操作和 release 均要求 HTTP 已停止。域管理 accessor 的操作为：

```sh
python3 "$console_service/app/service.py" access-stop --service "$console_service" --run '<运行ID>'
python3 "$console_service/app/service.py" access-start --service "$console_service" --run '<运行ID>'
```

这两行列出可用命令，不表示停止后立即重启的流程。命令经过冻结 controller 核对 accessor 域身份及实际终态；域执行 start 为单次出生，不能保证同一终态访问容器可重新启动。缺失容器、未知 daemon 或未确认效果保留原错误，不自动重建或重试。

解除登记时先关闭转发与 HTTP；独立 accessor 还须已确认停止。归档、本机或 runtime-readonly 接入不要求停止原生成执行。随后：

```sh
python3 "$console_service/app/service.py" release --service "$console_service" \
  --run '<运行ID>' --confirm-no-forward
```

`release` 移除当前恢复配置、保留 ID 墓碑与原登记回执，不删除文件或容器，也不释放实验资源域的 reservation。仅停止 HTTP 或 accessor 不解除依赖；仅 release 也不移除 named volume 的容器消费者。后续资源回收仍由实际实验 owner 按冻结合同办理，不用低层 Docker 清理替代门控。

服务切换先准备有效新根，再核实停止旧 HTTP 和任何自动启动入口，将旧配置、active/launch 与 journal 原件保存到新根 history，并显式退役旧权威 manifest。旧 journal 不混入新活动 journal；没有 stage/activate/rollback 命令或自动回退。新服务失败时保留新配置与具体错误，修复新制品，不自动恢复旧服务。当前服务及未退役的可恢复配置仍引用 Python、程序、现场 workspace/挂载和归档；回收前按真实 manifest 核对消费者，不能从旧格式扫描的“完整”推导无引用。

部署反馈使用实际登记的列表、已有 Issue/PR、会话与运行身份读取，保存 HTTP、CLI 与控制原始回执。读取成功、人工修改成功、模型采用指示和最终任务效果是不同事实；不要为设施检查发送测试评论、暂停或恢复模型。具体部署与验收身份进入相应记录，通用手册不维护“当前 PID”或登记项数量。
