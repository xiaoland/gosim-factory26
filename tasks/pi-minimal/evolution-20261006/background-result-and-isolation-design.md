# 后台结果与隔离验收生命周期：调查及最小方案

状态：用户已授权实施三项机械改进，并以本地自费 evo-github 实际运行验证。共享 baseline、插件接线及执行身份的当前进度归 packet.md；当前官网冻结包和运行不合入。本文保留已采用的因果分析、边界与实施依据，不以设计承诺替代实际验证。

## 2026-10-08实际运行暴露的遗漏与已授权修复

本地真实轨迹确认此前handle设计没有完整落地：bash启动content只有bg短ID，真实owner-qualified handle仅在details，provider模型结果通常只消费content；错误中的instance占位又导致字面拼接。新修复覆盖显式后台/自动转后台的实际文本返回，result/wait/stop直接消费同一真实handle；当前owner唯一且有manifest证据的短ID可解析，不能跨owner猜测。实际model-visible消费反馈与SDK读取details是不同依据。

受控停止再接续保留了workflow running元数据，却没有恢复普通child进程，父继续长wait。新修复以Pi completion owner实例识别普通工作的新进程接续，保已完成结果，不可恢复的未完成任务明确中断；独立async runner需按其process-instance真实存活判断，不能因父owner变化一律标死。服务name/端口/DB隔离不等进程控制隔离，宽泛pkill仍可能自杀/互杀；owned生命周期继续修；用户明确所有sub-agent不增加sandbox/权限控制，角色边界由职责/catalog和父委派选择表达，advisor不承接实施，不使用只读工具上限。

用户已明确授权共享baseline修复、核官网新ZIP复现并取消。实际owner/源码范围、无模型反馈和部署边界按packet当前紧急闭环维护；本地及官网不自动重启。原件见local-stop-analysis-20261008的README、child-tool-evidence及native。新补丁验收要覆盖content可复制handle和停止/重新载入后状态，不能再以加载成功/人工读取details代替。

两项共享源码修复已完成，实际当前producer21patch/57targets、vv/I15共同guard消费核对通过；model-visible Handle→真实操作result/stop和归档workflow中断反馈已取得，无模型调用，源码SHA与操作原件归 `pi-handle-owner-repair-20261008/handoff.json`。独立Linux runner出生身份/PID复用与managed宿主尚未实测，不把selected runtime当完整Linux交付，不热改既有官网/本地包。角色语义修复已真实发现验证：删除旧只读/角色tools限制，保全部原生能力，advisor仍咨询而非executor；所有role不额外权限隔离。

## 观察与因果边界

后台执行和结果消费是两种状态。冻结 PBB 在任务结束时写 job/log 并移出 activeJobs；Agent busy 时把完成正文留到 agent_end。连续工具轮只产生 turn_end，所以 aggregate subagent_wait 可以见到 active 项消失，却没有拿到 suite 正文。该现象不证明结果永久丢失。定向 subagent_wait 只查 subagent，错误 bg id 正常返回 Nothing to wait，是可明确修复的接口失败。

本轮 aggregate 等到了开发服务器 bg001，它没有声明 service；实际想等的 suite bg021 已结束。随后 pgrep 查询的模式也包含在 PBB 的 bash -lc 命令本身，不能用存在匹配进程证明 suite 仍活。最后 grep/tail 覆盖 suite 的退出码，PBB 记录 shell0是正确记录，不应推断应用验收成功。

隔离重置是另一条链。13:07:31按 pgrep 第一PID杀进程时 bg014 wrapper5820被终止，随后同路径数据库被删除复制。13:26真实node5823仍监听且日志28次 SQLITE_READONLY。强支持旧连接仍读已修改数据库、路径替换没有替换连接；缺少当时进程父子图与inode，不能把重建说成完全直接观测。源码没有启用WAL，当时目录只有主DB，WAL不是必要根因。应用已有 closeDb → removeDatabaseFile 的安全顺序，Agent shell 没有使用它。

PBB本身已通过 detached:true建立进程组，持久记录 pid/pgid；正常abort向整组发信号。此次按名字杀首PID绕过了该能力。现abort升级SIGKILL依赖 !settled，shell结束不一定证明孙进程全部结束；后续如果承诺“停止后可替换数据”，必须确认组退出，不能直接用job终态替代。managed宿主还拥有finishManagedProcess的退出回执，应复用而不是另建进程管理器。

## 推荐：先补原生PBB定向结果与控制入口

新增一个共享插件原生工具入口，操作限定为 wait、result、stop。它复用当前 PBB job manifest、日志、owner mailbox和进程组；不新增daemon。bash返回可直接复制的 owner-qualified handle，包含provider、当前owner instance及job身份，保留旧bg显示值用于追溯。持久结果读取要核当前Pi session归属，不只凭一个可重用bg数字。旧bg兼容只在当前owner明确唯一时解析；旧owner或错误namespace显式失败。

wait只等待指定任务，支持有界超时和AbortSignal；任务结束直接返回 outcome、shell exitCode、signal、正文有界摘要、完整日志路径及结果identity。terminal记录保留到运行归档，不依赖active列表，也不依赖自动完成通知先被模型消费。result不等待，返回running或完整terminal；unknown/missing/corrupt分别保留具体错误。服务也可result/stop，但默认aggregate完成合同继续排除service。

subagent_wait保持专用语义，对显式但未知id返回isError及 WRONG_HANDLE/UNKNOWN_SUBAGENT，而不是成功Nothing；无参数且确实无任务仍可正常返回。说明中指出PBB定向入口，工具schema与实际错误一起形成机械边界。无需先扩background-work v1：该协议严格拒绝未知字段，当前只有listActiveWork/reconcile，强塞terminal方法会影响所有消费者。

保留现有agent_end批次通知、error/willRetry处理与managed完成合同。主动查询是当前工具调用的响应，不调用sendMessage(triggerTurn)、不产生额外模型轮、不把终态重新加入active以阻止收尾。重复读取同一结果可返回相同identity；“模型已经理解结果”不应由读取接口虚构。自动通知可能随后重复给同结果，应携相同identity，首先接受有限重复而不引入全局已消费抑制状态。

stop按该handle请求owner整组停止，返回 requested 与 stopped 不同状态。确认组仍活时不能返回stopped；明确记录超时、权限失败、owner丢失。避免对未知/stale PGID自动发信号，沿现有显式stale控制合同；managed模式服从宿主所有权，不绕过宿主杀其他任务。run结束仍使用现有清理路径。

## 隔离验收的最小边界

现有 `materials/skills/agent-browser/scripts/with-service.py` 已提供独立进程组、占用端口拒绝、服务存活与check真实退出码、finally清理及回执。推荐将它作为验收入口的实际实现复用，不另写服务启动器；原生入口负责结构化参数和持久结果发现，脚本保留执行所有权。它的stop先等待父进程再检查整组，并向残留组KILL，比只等待wrapper更适用；当前KILL后只等待父进程，若新合同承诺整个组已消失，应补最终组存活核对或明确无法确认。health仍只负责ready，不能代表停止完成。本轮尚不需要通用fixture框架。原生PBB控制解决“杀哪一个服务”；service:true解决“服务器不应阻塞完成”，但不能判断任意命令究竟是不是服务，也不能自动修复既有数据准备逻辑。

每次验收优先使用新的隔离数据目录和显式数据库路径，保留交付DB不变；旧attempt服务用其handle停止并确认退出后再清理。不要在活连接下rm/copy同路径。若必须同路径重置，必须先完成服务停止；对SQLite，在线备份或完全关闭后复制更可靠，不能按只主文件拷贝推断所有journal模式安全。不得将本轮无WAL证据泛化为所有应用禁用WAL。

启动回执只证明所启动命令的生命周期，health200不证明端口属于它。最小操作证据是owned服务身份、明确DB绝对路径、旧listener退出、新服务日志/实际API响应；若要验证写路径，使用已授权隔离副本中的临时对象，不能对交付数据或活官网写入。公共工具不懂应用的GIVEN/WHEN/THEN，数据准备仍是Agent责任。

suite复合shell应保存执行器退出码再输出统计，并以该码exit；默认对任意bash启用pipefail会改变大量命令语义，不能作为此次统一强制修复。失败suite仍允许工具正常返回结构化terminal，但不得把shell0或报告文件存在等同验收通过。

## 备选与实施范围

若产品确实要求一个工具跨subagent/PBB/provider定向wait，可升级background-work协议，增加lookup/readTerminal/wait等能力和provider-qualified身份，迁移严格字段校验、两插件及managed消费者；这是更大的ABI变化。它应保留subagent输出/失败合同，不能把provider disappeared等同成功。推荐先采用PBB原生入口，实际有第二个provider需求再选统一协议。

源码范围是materials/npm的PBB/subagents共享补丁、共同producer最终target manifest与工具metadata；维护消费者为vv standalone和I15 managed。角色/模型/业务应用不合并。历史冻结包和本轮运行不改；pi-minimal历史入口不新增能力。需更新现有共享插件技能与durable技术说明，技能正文独立，catalog只入口metadata。

## 实际反馈计划

不写Factory/Braid测试或模拟probe。用真实Pi ExtensionRunner无模型构造核工具参数/元数据/错误合同，用真实生成应用的隔离副本完成一组实际生命周期操作：启动service并取得handle；启动真实suite并保存原退出码；在busy工具轮按handle取得已经结束的exit/body且服务器仍活；错subagent id明确失败；终止owned服务后确认listener与组退出；新隔离DB启动并进行一次公开旅程，交付DB哈希不变。验证managed分支需实际宿主运行条件，无此条件不能用standalone结果冒充。

另可有界对真实应用副本重现旧连接下同路径替换DB后的具体错误、记录SQLite扩展码/inode/进程组，再以正常close-stop新目录重试。这是区分根因的应用操作，不是新增开发基础设施测试。当前调查未执行此实验，结论仍保留强重建边界。

## 证据入口

原件根为runs/pi-minimal/evolution-20261006/e2e-assembly-repair-20261008/mcp-guidance-20261008。pbb-namespace-inquiry/frozen保存实际插件：pi-background-bash/extensions/background-bash.ts的spawn593、abort623、provider979等；pi-subagents/src/api/background-work.ts定义v1严格协议。bin/pbb.js已有instance身份、status/tail及mailbox/stale控制。miswait-reset-inquiry/README.md、selected-events.json给本轮时序；722f开头运行的diagnosis-20261008-131841-authorized-retry/semantic-evidence提供bg021.json/log、init_db.js、native-managed.mjs与suite源码。精确源SHA沿对应source-identity/mechanism-identity记录，不用当前源码冒充冻结版本。
