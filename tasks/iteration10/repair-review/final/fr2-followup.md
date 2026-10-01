# FR2合并恢复增量独立复核

当前结论：原FR2的祖先恢复缺口及本复审发现的未发布prepared显式head条件均已在源码闭合；最新局部复核未发现新增确定阻断。实际M→D恢复与拒绝行为仍未验收。这里只评本增量，不涉及Pi补丁、其它目录或模型行为。

首次读取基线为 `sources/braid/src/objects.rs` SHA-256 `b4b3324e3b4a65b7a9bb1c9f54344ecbf9f7c47b4a35a19e2d1eeeb10447e398`，补修后局部复核基线为 `207c7a157dc661b1c9830b1718cdc87d77723e4c10b0701a3ee7de6345433a7a`；另读 `cells/merge-recovery-fr2.md` 与本地合并契约。未编译、运行测试、探针、Git实验或修改源码，仅写本文件。cell的cargo check是实现方既有记录，不是本轮独立行为验收。

## 已消费的复审发现：未发布prepared重试忽略显式head条件

本节反例描述首次基线，当前补修已消除此问题，最新核对见末节。

`merge_with_match`现在在draft及expected_head检查之前读取prepared intent，存在就直接调用 `apply_merge`。该调用既可能仅结算已发布结果，也可能真正发布尚未发布的M，不能一律视为幂等读回。

具体静态反例：原intent已持久化，冻结head为H、目标base为B，但进程在Git更新前中断；重试时源仍为H、目标仍为B。调用者执行 `merge --match-head-commit X`，其中X≠H。当前prepared分支跳过比较，而apply_merge的原CAS只验证源等于冻结H、目标等于B，因此发布M并返回成功。该次明确不匹配的条件没有阻止新Git写入，违背现有CLI和 `local.md:86` 的源头匹配契约。这是可由源码决定的行为变化，尚未实跑，不归因旧两题。

竞争边界：若M已经在目标M/D历史内，仅补齐原收据时不应要求当前head仍为H；否则会重新引入FR2希望消除的恢复依赖。若没有prepared，现有expected比较仍成立。问题仅是同一prepared分支把“恢复已发布事实”和“本次仍要发布”混在一起，未保留后者的调用约束。

更小的修法是让显式expected条件到达真正发布未发布intent的入口：发布前要求所给expected与冻结head相符，再由既有Git ref事务验证源仍为冻结head、目标仍为冻结base；自动恢复未提供expected时沿原授权intent推进。已发布M/D则只结算，无需重新读取当前正文、当前head或重生成merge。具体接口由主线整合，不需要再建一种merge状态或重试框架。

## 已核对成立的边界

| 条件 | 当前机制及判断 |
| --- | --- |
| 当前目标就是M | 不进入Git更新分支，直接按原intent结算；保持目标不动。 |
| 当前目标D为M后代 | `graph_descendant_of(current, merged)`方向正确；保持D，PR收据继续保存M，activity区分M与当前D，避免把D冒充该次merge。原FR2的假冲突分支已消除。 |
| 当前目标不含M且不等于冻结base | 拒绝并持久化conflict，不关闭Issue，不挪动ref。不会以“目标含当前head”代替M的发布正证。 |
| 当前目标仍为冻结base | 仍使用冻结source ref/head与base进行Git verify+CAS；源改动会拒绝发布。首次基线的expected条件缺口现已补齐，见末节。 |
| CAS失败后目标被并发推进到含M的D | 重读目标，并用与初始恢复相同的M祖先判定；不因客户端错误字串否认已经发生的发布。 |
| CAS失败后目标仍不含M | 保留发布错误，intent置conflict并返回；不执行PR/Issue结算。 |
| 后来正文/head/base改变，但M已发布 | prepared重试先apply，不重新解析正文或准备merge；`close_merge_issues_in`仍只消费持久化closing_issues。被冻结的关闭义务不会被新正文偷偷替换。 |
| 重复apply或重复merge | applied直接返回；PR已经MERGED返回现有merge_commit，不重复发关闭事件。已关闭Issue也不重复transition。 |

仍有的证据限制：以上是当前函数与直接调用链静态推导；尚未观察真实M→D崩溃恢复、未发布拒绝、冻结Issue关闭或CAS竞态。Git祖先读取和SQLite提交并非跨系统原子事务，本次只履行已存在的冻结意图/CAS契约，不新增任意外部force-push后的绝对一致性承诺。后续最小证据应记录原intent、目标M/D关系、实际ref是否变化及关闭目标，不用重新全跑44项或构造设施测试。

## expected_head补修局部复核

只重读三个apply_merge调用点及发布条件，没有重复整项复审。`merge_with_match`的prepared重试和初次prepare路径都传入本次expected_head；`recover_merges`传None。`apply_merge`仅在current等于冻结base、即将尝试更新Git引用时检查expected是否等于冻结head。检查失败直接返回，尚未调用Git、更新intent或执行关闭，因此原prepared和冻结closing_issues保持不变。

匹配时仍由既有Git ref事务验证当前源等于冻结head、当前目标等于冻结base；传入expected并未取代CAS。如果目标已为M或其后代D，则不进入发布分支，后来的源head变化不会阻止原事实结算；非祖先目标仍沿既有冲突路径拒绝。自动恢复None不增加一次新源选择，仍发布或结算原冻结意图。

此局部修复正好区分“本次还要写ref”和“只补已发布收据”，没有新增状态或重算正文。可以将FR2状态记为“源码已修，独立静态增量复核无新增阻断”；没有运行测试、探针、编译或实验，真实操作条件保持未证。
