# I13 上下文更新实施预演

2026-09-30。只读源码预演；没有修改源码、启动运行、调用模型、编译、测试或提交。唯一新增材料为本报告。依据为 [已认可策略](context-update-policy.md)及[修复方案第三、四部分](repair-design.md)。I12继续暂停。

源码身份：`sources/braid` HEAD 为 `0712a58d0e5f7af225473d6c48c4aa740c20dfbf`，存在未提交修改，本报告描述读取时的工作树，不把 HEAD 当成完整实现身份。以下路径均相对于 `sources/braid`；实施前应确认并保留既有修改。

## 结论与改动边界

现有本地路径可以沿 `objects.rs` 的事务、Writer、事件与收件关系实现，不需要新增事件框架或数据库迁移。确定性缺口有四组：title被当成description；评论维护直接生成Invalidate；link/unlink直接生成Invalidate；部分关系和评论维护目前没有相应增量通知。只把Invalidate改成Wake不能完整满足规则，因为会丢失收件范围或留下重复通知。

没有发现活动会话因投影hash变化自行重建的后台比较。hash用于记录实际物化内容和休眠会话复用判断；后者是由重新开放或定向联系启动的生命周期路径。必须保留最新投影及hash，不能为了避免重建固定旧快照。未知provider执行结果的恢复直接创建reset，属于保留的生命周期行为。

跨项事实需要收窄：PR投影包含开放的关联Issue的标题、描述、状态、负责人，但**不包含关联Issue评论**；父子Issue仅投影对象引用，不展开对方描述。因此关联Issue评论变化目前让PR重建是多余失效；关联Issue描述变更应只向真正包含该描述的PR重建。父子关系、title、link/unlink的变化应增量告知相应成员，并在未来合法物化时读取最新关系。

## 入口清单与已有接口

| 现有入口 | 源码位置与实际行为 | 实施处理 |
| --- | --- | --- |
| 对象title/body编辑 | `objects.rs::edit_with_parent_and_assignees`，约862–879：title不同或HTML注释过滤后的body不同均调用`changed(Invalidate, true)`；`true`令Issue关联PR也失效。 | 分别计算title变化、可见description变化。仅后者Invalidate；title仅增量。title+description同时变化仍只依真实description决定失效。 |
| description跨项传播 | `objects.rs::changed`，约695–716：Issue且description=true时向全部active association PR发`cross_surface` Invalidate。 | 保留共享传播入口，只在真实description变化调用；匹配投影的开放Issue依赖边界。PR有自身描述变化时仅自身重建，Issue侧没有嵌入PR描述。 |
| 创建评论/回复 | `comment_reply_in`，约969：`discussion_changed(Wake)`后调用`direct_mentions`。 | 保留正常增量输入和@规则。 |
| 编辑评论 | `edit_comment`，约1080–1115：可见且未折叠评论为Invalidate，否则Wake；新@仅在可见且未折叠时处理。 | 所有评论编辑均不重建；保留现有可见性及新@投递条件，不把隐藏文本突然广播。 |
| unhide/delete | `comment_visibility`，约1120–1150：实际生命周期/原因变化时Invalidate。 | 更新原状态与活动，改成合适的增量收件。delete清空正文，通知必须说明删除而不是诱导读一个仍有正文的对象。 |
| hide及原因更新 | `hide_comments`，约1153–1180：先验证整批，再逐项变更、Invalidate。 | 保留事务全批验证和去重，不逐CLI打补丁；实际变更增量通知。重复无变化不造通知。 |
| resolve/unresolve | `resolve_comments`，约1184–1238：根`resolved_through`变化时Invalidate。 | 保留折叠截止及新回复可见的语义；增量通知。第三组CLI修复将根ID收窄，须在这个共享入口合并修改。 |
| link/unlink及创建PR关联 | `link_in`，约1660–1695；`link`和`create_pr_with_profile_and_refs`均调用：双方followers通知，再PR Invalidate。 | 删除关系失效，补齐两侧负责人增量，避免显式followers重复收件。创建时仍保留Assign及新PR工作Wake。 |
| parent变化 | `edit_with_parent_and_assignees`，约840–857：记录子项、旧父和新父activity，但仅对子项`changed(Wake, false)`。 | 不失效；真实变化向子项、旧父和新父受影响成员增量通知。当前只写父项activity，不等于父成员已知。 |
| ready/draft | `ready_with_undo`，约1733–1747：followers及自身Wake，无Invalidate。 | 保持分类；收件共用调整要避免添加第二份负责人通知。 |
| reaction、subscribe、close/reopen、merge | `objects.rs`对应入口未生成内容Invalidate；close/reopen、merge走Lifecycle，部分有普通Wake。 | 不把这些生命周期行为过滤为Noop，不扩大本次政策到停止/创建会话。 |

已检索`src`所有`EventKind::Invalidate`；本地内容生成点均在上表及`discussion_changed`内部。`queue`和`provider`未发现其它Invalidate分类入口。`store`还有`schedule_cross_surface_invalidations`的SQL生成点，见下节。

**发起者识别可直接复用。** `objects.rs::writer`（约235–243）以当前turn或`cli_binding_id`联到provider session、agent及assignment，返回`Writer { group: agent_id, node: work_item_node_id, turn: turn_id }`；必须是有效活动执行，旧binding拒绝写入。`member_login`（约244–250）从Writer的agent找到具体assignment成员名。人工`--external`调用没有Writer。不要比较profile/model或被编辑评论的历史作者。

`emit_with_id`（约627–691）只将发起项自己的Wake改成OriginEcho；自身Invalidate原样保留。description自身重建按已认可政策继续保留，不能将所有自身事件统一OriginEcho。对评论/元数据的接收方，应在收件循环用`member_login(writer)`排除实际操作者；再保留现有OriginEcho兜底即可。即使操作者编辑他人评论，也排除操作者，不排除原作者。

`discussion_changed`（约1034–1077）已经有可复用的收件SQL：当前负责人、显式active关注者、同thread历史参与成员；参与者显式退订优先。它目前只有created/edited进入该循环，hide/unhide/delete/resolve/unresolve只有失效没有增量。其Invalidate分支还无条件向关联PR失效。最小共享改法是移除讨论失效分支及kind参数，让需要传播的维护动作走同一收件选择，reference携带动作及读取入口；创建/编辑的新@仍留在既有`direct_mentions`。

`deliver_comment_to`（约989–1024）按具体成员找其当前项；开放项Wake，关闭项Mention/direct_contact；记录`local_comment_delivery`及assignment revision。已有blocked/retired及改派不可达原因必须保留。评论维护可以复用这条投递路径，但需让reference表达维护动作，不能让所有hide/delete消息仍显示成“评论 #N”。不要另造通知系统。

`notify_followers`（约261–276）只选显式关注者，且主动跳过源项负责人及操作者。现有owner通常另由`changed`/`link_in`事件覆盖，因此不能简单删除Invalidate而不补owner。建议将“当前owner+显式关注者，排除操作者、按成员去重”的元数据收件集中于这个已有共享函数，再删除对应调用点的重复owner Wake。description维持owner Invalidate、followers增量，须显式保留该差别，不改变成所有followers重建。

## 存储、调度与物化：没有hash旁路，保留生命周期

`store::ingest_event_transaction`（约2070–2300）保存调用方已经选定的kind。`canonical_objects`版本/digest比较只做stale/duplicate判定，不根据“整个对象digest不同”升级成Invalidate。本地`emit_with_id`传`object_digest=None`、`visible_body=None`、`cross_surface_invalidation=false`，所以不会进入另一个description传播通道；origin实际为`local`，不能误认为其已被`origin!='agent'`过滤。

`store::schedule_cross_surface_invalidations`（约2303–2389）是保留的历史Ingress接口：只有issues/edited/open、提供visible_body、cross_surface标记且非agent origin，才比较`issue_context_sources.visible_description`并向关联开放PR生成Invalidate。本地CLI不走此分支。若未来接入该Ingress，分类入口也须只在真实description变化设置标记；本轮无需替它加新的远端事件系统。

`store::context_reset_work_item`、`context_reset_events`（约4760–4855）选的是pending Invalidate；cross_surface还须所属batch为runnable。`begin_context_reset_transaction`将这些event转resetting；`refresh_context_reset`只追加新的失效事件。它们不比较投影hash。`group::dispatch::materialize_context_reset`每次重新读Issue/PR canonical对象，再render、记录revision、启动新会话；因此评论整理可立即更新对象，但只在下一次真实重建投影中生效。

`context::render_context`（约277–298）hash最终文本；`context::record_context_revision`及`store::set_context_revision`（约1915–1933）只记录revision，不生成事件。`group::dispatch`约209–240在生命周期重新激活时仅当profile、context和instruction revision均相同才resume sleeping session，否则start最新上下文。这意味着关闭后的成员因真实定向联系/重开而恢复时，title/comment更新可能令它创建新物理会话；这是恢复时避免复用过期快照，不是活动会话内容失效。取消hash判断会违反“未来恢复读取最新对象”。

`store::fence_session_and_request_reset`（约5612–5640）为unknown执行结果直接写materializing reset；`mark_turn_terminal`（约5704–5752）处理失效与结束竞态及unknown恢复。保留这条路径、离线恢复、Assign/Unassign和生命周期调度。不要在`begin_context_reset`前设一个“非description全部拒绝”的全局门禁。

**混批不会天然吞普通输入，但需要实际验证。** `context_reset_events`仅选择Invalidate；`complete_context_reset`约5275–5320仅消费reset所关联失效事件，且无continuation时只有batch内已无pending event才消费batch。`batch_references_connection`约5949–5970选择非Invalidate pending输入并校验当前recipient revision。真实描述失效与评论Wake同批时应分别重建和投递，不能把整个batch或同一Writer的全部事件标成OriginEcho/consumed。normal turn claim和steer消费仍沿原有机制，不额外编写“混批框架”。

## 跨项及可见description的接口约束

`objects::issue_in`、`pull_request`（约1355–1419）从当前表重新组装关系和原文。`context::render_issue_at`（约381–405）对普通Issue显示父子/PR引用、描述和讨论；`render_pull_request`（约407–440）只展开开放关联Issue描述，`associated=true`省略其讨论。应按这些实际依赖决定跨项事件，不能按整个canonical snapshot有变化判断失效。

父项description变化不会影响子项描述投影，子项title变化会让父项对象引用过时；PR title变化也会让关联Issue引用过时。这些都应按既有关系增量提示读取最新对象，不重建。当前`changed`只支持Issue描述→PR；parent编辑只有activity，title+body编辑只通知本项followers。可在既有`changed`/关系事务内按受影响对象通知负责人及显式关注者、去重，避免把关联对象的所有历史评论作者升级成订阅者。开放关联Issue描述变化重建PR；关闭Issue仅保留编号引用，不应因其描述变化重建PR。

description可见变化当前只使用`filter_html_comments`（`context.rs`约583）；同批details折叠落地时，**描述变化比较与实际投影须共用同一个正文可见化函数**。仅修改details内部隐藏正文、summary不变，不应在renderer已隐藏正文后仍因旧比较触发重建。summary变化、正文实际清空仍为真实描述变化。比较正文可见化结果即可，不比较含title/评论/预算分档的整个rendered hash，也不因末端预算恰巧省略描述就失去description失效语义。

## 建议线性实施顺序

1. 与折叠实施者确定已有`context.rs`正文可见化函数的单一接口；renderer和description比较一起使用。先保留CLI完整原文。
2. 在`objects.rs::edit_with_parent_and_assignees`分开title/visible description布尔值，收紧`changed` description→PR依赖条件；title+description不拆成两次写入事务。
3. 收敛`notify_followers`的元数据owner/follower投递与自排除，并同步修改`changed`、`link_in`、parent和ready调用，按同一具体成员去重；描述owner重建仍保持单独语义。
4. 将`discussion_changed`收敛为增量通知，所有评论维护共用收件SQL；复用`deliver_comment_to`并传入动作reference。保留新@、显式退订、改派及不可达回执，与resolve根ID修复同点整合。
5. 更新`store::EventKind::Invalidate`注释及权威`docs/20-product-tdd/context.md`、`local.md`、`lifecycle.md`中真实受影响的行为说明；不改存储schema或reset状态机，不加新测试/探针。
6. 开工获批后编译，按下表执行获授权实际操作，并归档对象、事件、回执和原生身份。模型运行范围另行记录；本次预演不执行。

## 实际操作验证矩阵（尚未执行）

建立小范围实际Braid运行：A为Issue负责人，B为关联PR负责人，C为同thread参与者/显式关注者，D退出关注；成员均有可追溯原生身份。以宿主操作及当前成员的真实CLI操作分别验证。每项保留操作前后对象读回、`events`/`wake_batch_events`/`local_comment_delivery`/`context_resets`只读快照、`sessions.json`和真实`physical/*/context.md`、turn输入。没有新采样不足以证明没有reset，必须核对reset记录和物理session身份。

| 操作 | 应观察的结果 |
| --- | --- |
| A创建回复、编辑自己的评论、编辑C的可见评论 | A无增量自回送；符合关系的C及负责人收到真实增量；D无普通参与通知。全部无内容reset。新增@仍单次送达。 |
| A对根/回复hide、改hide原因、unhide、delete | CLI与Console状态立即读回；维护动作给其它原有收件成员；delete墓碑及原始结果明确。A无自通知，PR无评论跨项Invalidate，物理session保持。 |
| A批量resolve/unresolve、重复执行不变操作、resolve后新回复 | 根/截止/改变数与回执一致；重复不造更新；新回复可见并投递。无reset。误传回复ID按第三组接口拒绝，不部分写入。 |
| A仅title、仅parent、link/unlink、ready/draft | 无内容reset；owner、旧/新关系侧及显式关注者得到必要增量，无双份；最新CLI及未来projection反映真实关系。 |
| 人工仅title/评论维护 | 没有模型发起者排除，必要成员都获知；无内容reset。 |
| A修改description；人工修改description | 自身原重建语义保留；开放且依赖该Issue描述的PR重建；父子Issue不因描述引用之外变化重建；description新context正确。 |
| description原文相同、仅HTML注释、仅details内正文、summary变化、清空正文 | 前三者可见description不变时无reset；summary及实际清空触发。CLI完整原文仍可往返。 |
| title+description同一次edit；description+parent/指派同事务 | 前者仅真实description控制重建，元数据不重复owner消息；后者必要Assign/停止/新会话及父关系通知都保留，不能被自排除一起吃掉。 |
| description Invalidate与他人评论Wake在同一debounce窗口，覆盖idle及running | description进入reset；他人Wake及回执保留，重建后仍实际投递；正常终态到达的continuation决定沿用既有判断。 |
| 两个Issue关联同一PR、同Issue关联两个PR；其中一Issue关闭 | 仅开放描述依赖更新令关联PR失效；title、关系及评论都不重建；另一Issue的真实输入不被去重消除。 |
| 关闭/休眠后先维护title/comment，再真实定向联系或重开 | 生命周期允许恢复；新物化读取最新状态，不人为固定旧hash。必要时新session是恢复结果，不将其误算为活动内容reset。 |
| 取消/重新指派、provider真实unknown及离线恢复 | 原有停止栅栏、具体成员代际、新CLI binding、未知执行错误及新物化完整保留，不因description-only政策被禁止。 |

本次没有需要改变已认可产品方向的阻塞。所有“应观察”都是实施验收目标；上述源码事实不构成新行为已经通过验收的声明。

## 补充：同一休眠成员的恢复连续性

主Agent复核指出：同一可恢复成员仅因title/comment导致完整投影hash不同而创建新provider session，仍是非description变更造成重建；不能以“恢复生命周期”豁免。这个纠正成立，覆盖前文“休眠恢复hash校验须原样保留”的判断。真正的新指派、instruction/profile变更、原生会话不可恢复另行处理；普通字段更新不能破坏已有原生历史连续性。

**接口事实。** `group::dispatch`约209–240确实以完整`session.context_revision == rendered.revision`决定是否尝试resume，失配直接start；provider端没有此要求。`SessionManager::resume`（`group/session_manager.rs`约100–135）和`SessionFactory::resume`只需要既有id、profile、instructions、CLI binding，不接收新的context正文；成功后校验返回id不变。`ProviderAgentSession::resume`（`provider/session.rs`约140–163）只调用`resume_session`，不会发送替换context。Pi的`resume_session`（`provider/pi.rs`约345–386）用确切原生session文件启动并核对路径一致，Codex的`resume_session`（`provider/codex.rs`约360–390）调用`thread/resume`并核对thread ID。因此去掉**完整投影hash作为resume资格**在接口上成立，不能同时把当前新投影hash冒写成已resume会话的实际context revision。

dispatch一处删除比较还不够。`store::complete_work_item_reactivation`约3832–3843在resume分支再次要求数据库旧`context_revision`等于传入参数；dispatch目前传的是当前rendered revision。resume成功后应传回旧session revision，并保留provider session的旧revision；新start才记录当前revision。`work_items.context_revision`表示最近真正采用的上下文，不应在“仅计算了新canonical投影、未把它送给resume会话”时调用`record_context_revision`覆盖。当前状态仍从对象数据库即时读取，CLI与后续新start读取最新canonical即可；resume通过既有Wake/定向通知获知增量，而非重新注入完整材料。

**判断description是否变化，推荐复用既有pending事件，避免新增历史diff协议。** 完成前述分类后，内容Invalidate具有“只有真实description变化”的不变量；然而当前`objects::emit_with_id`约648把休眠成员的Invalidate降为Noop，`store::prepare_work_item_reactivation`重开分支约3775–3788又消费pending直接Invalidate。应在同一事务选中确切休眠成员时，先读取并携带其尚未应用的description失效事实，再消费旧描述事件；dispatch用该事实代替全投影hash比较。

最少共享改点为：

1. `emit_with_id`对存在真正可恢复sleeping assignment/session的目标保留description Invalidate为pending，仍不触发休眠项即时采样；没有有效成员的目标继续Noop。description事件可用已有`events.recipient_revision`记录当前`assignment_revision`，避免前一代指派的失效被下一代采用。关联Issue真实description变化沿相同入口覆盖休眠PR，不因尚无runnable batch而丢失这个事实。
2. `prepare_work_item_reactivation`在既有事务内，根据已选assignment和pending Invalidate判定`description_invalidated`，作为`SleepingProviderSession`或`AgentMaterialization`的一个布尔值带出。这个恢复判断不要求cross_surface batch已runnable，因为恢复已获真实输入驱动，需先采用当前描述；活动reset仍保持原debounce规则。只结算本次新start实际覆盖的描述失效，勿消费混批中的评论Wake。直接联系路径也要结算描述失效，不能仅处理reopened分支。
3. dispatch resume资格变成同一选中成员、profile/instruction相同、没有上述description失效、原生会话确实可resume；title/comment/relationship投影hash不同不排除。description失效则start当前投影；真正新指派仍走既有创建路径。`complete_work_item_reactivation`及revision记录区分resume旧上下文与start新上下文，维持原SQL并发前置条件而非删除全部身份校验。

这里不需要新数据库字段：`events.kind/lifecycle/recipient_revision`、`local_items.assignment_revision`、`assignments`身份以及`provider_sessions`旧context/instruction revision已经能表达“同一成员是否有未应用description变更”。不过要明确实施顺序：先保证description-only分类，才可把pending Invalidate作为描述信号；当前工作树中的title/comment Invalidate不能据此推断旧休眠会话曾有description变化。I13新运行可建立该不变量；不能据此迁移或修改I12现场。若未来要兼容旧状态，则旧事件来源不能准确区分的情况须另议，当前授权没有这项迁移要求。

**恢复失败的事实边界。** Pi确切文件不存在时dispatch已有明确start分支；Pi路径查询、Codex native-home定位和resume id校验也可提供具体不可恢复原因。`ProviderAgentSession::resume`将超时、连接断开、启动错误映射为Deferred，这些不证明旧会话丢失，不能自动换session规避错误。其余失败目前返回错误而非普遍自动start。保持原错误/身份及恢复路径，不引入“任何resume失败都start”的新兜底。新方案的实际resume成功率、在途更新竞态、恢复增量投递仍需获授权操作取得证据，本次仅核实接口可行性。

**验收授权补正。** 前文“建立小范围实际Braid运行”的措辞只是观察覆盖草案，不授予新建运行权限，也不能为验证而建立模拟或专用模型测试run。矩阵只能选取已获授权真实运行中的自然操作/经授权操作，检查title/comment维护后的同一原生session连续性，以及真实description更新、新指派和真正不可恢复的区别；不修改I12现场。不满足观察条件的格子保持未证，并在实际运行范围复核时说明，不以自建测试补齐。
