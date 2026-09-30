# T14 | turn 9d503498-7836-4a7e-907a-caf568f147fc | startedAt 1788242971.169648


## userMessage | message 9d503498-7836-4a7e-907a-caf568f147fc


我同意观察「invoice eventually delivered」是正确的，但是你选择让系统暴露job state、event log，我会再次argue说，直接观察目标邮箱的inbox或者邮件服务器的日志是否有invoice，应该更加合理（也就是“端到端”），但其实这个问题我们的店面讨论测试分层的时候已经给出了解决方案，我们可以增加对job state的测试来解决。
哦，不，你是对的，你在说的是observerability，那当然要“暴露”这些关键状态用于debugging。
其它的我也理解了，这很到位；还提供了很多实用的SOP；也充分考虑到trade-off，明白过犹不及的道理。
我同意可以往这个方向进行，但我个人会有一种停在这里，等后续我们有更多真实案例，再通过归纳的方式来完成/完善「一次 feature 从 requirement 到 production，究竟应该怎样建立它的 assurance plan」会更好；而且我们还得警醒assurance plan这个凭空出现的概念。

## agentMessage | message 92191a81-ae42-40db-aca4-140d0783342f


是的，而且你刚才对 invoice 的自我修正其实又帮我们补上了一个很重要的维度。

`invoice eventually delivered` 的最终验证，理想情况下应该尽量观察产品世界里的真实结果，例如目标邮箱确实收到邮件。这是 **acceptance evidence**。

而：

```text
JobCreated
JobRunning
InvoiceGenerated
MailSubmitted
```

主要解决的是另一个问题：

> 如果最终结果不成立，系统到底在哪里偏离了正确轨迹？

这是 **diagnostic evidence**。

两者不要混淆：

```text
Product requirement
    ↓
最终 observable outcome
    ↓
Acceptance evidence
    ↓
“产品成立了吗？”

与此同时：

execution trace / internal state / logs / events
    ↓
Diagnostic evidence
    ↓
“为什么成立 / 为什么没成立？”
```

这也进一步解释了我们前面所谓“互补证据”的杠杆。

如果只有：

```text
Inbox 没收到 invoice ✗
```

证据的产品语义很强，但诊断能力弱。

如果只有：

```text
InvoiceDeliveryJob.state == succeeded ✓
```

诊断信息不错，但它不能充分证明真实产品结果。

两者组合：

```text
job succeeded ✓
SMTP accepted ✓
target inbox ✗
```

一下就大幅压缩了故障空间。

所以以后设计 verification system 时，可以有意识地区分：

> **我是在增加 acceptance confidence，还是增加 diagnostic resolution？**

一个测试/observer 两者都不增加，就很可疑。

---

至于 **“assurance plan”**，你的警惕也是必要的。

这是我为了描述“一个 feature 从需求到生产所需要的一组验证活动”临时使用的工作标签，不应该未经论证就把它实体化成：

```text
每个 feature 必须有一个
AssurancePlan.yaml
```

或者突然假定软件工程里存在这样一个标准对象。

这其实是我们整个学习过程中需要持续防范的一种错误：

> **因为我们需要表达某种现象，就过早创造一个名词，然后开始围绕这个名词设计体系。**

很容易变成 ontology-driven engineering。

更好的顺序正如你说的：

```text
真实 feature
↓
设计与实现
↓
遇到 verification / acceptance 问题
↓
观察反复出现的结构
↓
归纳共同模式
↓
如果确实有稳定结构
↓
再给它名字
```

这和我们处理 regression bug 的思路其实非常一致：

> 不要见一个案例就永久固化一个 artifact；先寻找它背后的更一般结构。

所以我赞成现在**不要定义一套完整的“assurance plan 方法论”**。

---

事实上，到这里我们可以把目前真正站得住的东西盘点一下。它们不是一个“大框架名称”，而是一组已经经过我们讨论推导出来的原则：

```text
Product intent 与 specification 之间必然存在解释偏差。

验证需要：
- test selection：测什么
- oracle：怎么判断

Specification 更应该收拢“正确行为空间”，
而不是主要枚举历史错误。

不同 verification boundary
提供不同性质和成本的证据。

测试应该形成互补证据，
而不是在不同层重复同一种 assertion。

测试价值必须考虑生命周期成本：
执行、延迟、维护、诊断、可靠性、语义耦合。

优先：
semantic coupling 高
implementation coupling 低。

现实 dependency 足够便宜时：
prefer cheap reality over elaborate simulation。

系统本身应该容易：
control / observe / reset / reproduce。

最终结果提供 acceptance evidence；
内部状态与 trace 提供 diagnostic evidence。

开发环境提供预防性证据；
生产环境提供现实世界证据。
```

这已经是一套相当有实际判断力的 mental model。

我认为现在反而应该**停止继续抽象**。

否则很容易产生漂亮但未经实际压力测试的理论。

接下来更适合进入“案例驱动阶段”：以后遇到一个真实 feature、一次 AI 修改、一个 production failure、一个难写的 E2E、一个不得不用 mock 的 dependency，我们就用目前这些原则分析它。经过几个不同类型的真实案例以后，再回过头问：

> 哪些步骤反复出现？哪些 artifact 真的值得长期存在？哪些东西可以自动交给 AI？

那时再归纳“一次 feature 如何从 requirement 可靠地走到 production”，会扎实得多。

而在系统学习的主线上，我们其实也已经走到了一个很好的暂停点：**Verification 的基本理论、测试选择、测试分层、成本模型和 testability 已经连起来了。**

下一块大的主线，我建议届时进入 **TDD**。不是重新学习 Red-Green-Refactor，而是用我们现在这套模型重新审视它：

> 为什么“先写验证条件”可能改变设计质量？它什么时候成立，什么时候会把 specification 错误地冻结在局部实现上？在 AI Coding 中，TDD 又应该变成什么？

这样会比一开始直接学 TDD 深很多。