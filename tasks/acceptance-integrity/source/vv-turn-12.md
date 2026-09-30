# T12 | turn e1ff5800-7c22-458d-99b5-76032259ec49 | startedAt 1787917543.951017


## userMessage | message e1ff5800-7c22-458d-99b5-76032259ec49


是的，我们按这个方向继续。而且这还提醒我，我们的主题是验证、验收，目的是保障软件在AI Coding时代下可靠地迭代。所以我们的范围还不仅仅限于开发时（事实上已经向前蔓延到设计时），还会蔓延到生产时。

## agentMessage | message 45ee7930-d3d9-4c2e-8b6e-2c06bc7d9fd0


对。这样一来，我们研究的对象其实已经不应该叫“测试体系”，而更接近：

> **Continuous Assurance：如何在整个软件生命周期中持续获得“产品仍然满足意图和约束”的证据。**

Testing 是其中非常重要的一部分，但不是全部。

而且这进一步说明为什么我们之前从 Product intent → specification → oracle 开始是对的：如果从 `unit test / integration test / E2E` 开始，很容易把视野锁死在开发阶段；从“证据”开始，就会自然一路延伸到生产环境。

可以先建立这条主线：

```text
Product intent
      ↓
Design-time specification
      ↓
Development-time verification
      ↓
Pre-release validation
      ↓
Deployment-time verification
      ↓
Production-time validation
      ↓
真实产品反馈
      ↓
Specification refinement
      └──────────────────↺
```

这里每个阶段回答的问题不同。

设计阶段首先问：

> 我们到底要求系统满足哪些性质？

产物可能不是测试，而是：

```text
domain invariants
API contracts
state model
acceptance criteria
latency budget
failure policy
SLO
security boundary
```

这也是为什么验证工作会“向前蔓延”到设计阶段。

一个很重要的例子是 latency。

如果产品要求：

```text
user action → useful response < 1s
```

你不能等软件写完之后再第一次考虑它。

可能需要在设计阶段分解：

```text
total budget: 1000 ms

browser/network     150
API gateway          50
application         200
database            150
external service    300
render              150
```

现在“验证”已经开始影响 architecture。

所以 specification 不只是用于测试已有实现，也会约束设计空间。

---

开发阶段就是我们已经讨论的：

```text
static
property / unit
integration
component
E2E
performance
```

这些最大的优势是：

> **失败发生在真正用户受到影响之前。**

因此它们是便宜的预防性证据。

但开发环境始终只能模拟现实。

再逼真的 staging，也无法完整复现：

```text
真实数据分布
真实流量
真实网络
真实用户行为
真实第三方服务
真实机器资源竞争
长时间运行产生的状态
```

所以最终一定存在一个 verification gap：

```text
Test environment
       │
       │ 无法完全证明
       ▼
Production reality
```

这意味着生产环境本身必须进入验证体系。

---

但生产验证和开发测试有一个根本区别：

开发测试可以说：

```text
失败了，没关系。
```

production 不行。

所以这里多了一个新目标：

> **不仅要发现错误，还要限制发现错误时造成的 damage。**

于是会自然产生一组工程机制：

```text
feature flags
canary deployment
progressive rollout
shadow traffic
automatic rollback
circuit breaker
rate limits
blast-radius control
```

这些看起来不像“测试”。

但从我们现在建立的理论看，它们明显属于 assurance system。

例如：

```text
AI 修改搜索服务
      ↓
所有 pre-production tests ✓
      ↓
deploy to 1%
      ↓
observe:
  error rate
  p99 latency
  conversion
  zero-result rate
      ↓
good → 10% → 50% → 100%

bad → rollback
```

这实际上就是一次实验：

```text
Candidate implementation
        ↓
真实环境
        ↓
Production oracle
        ↓
continue / rollback
```

---

这里出现一个很漂亮的关系。

我们之前说：

> E2E 具有很高的 semantic fidelity。

但 production 的 fidelity 更高。

因为：

```text
unit
    ↓ realism ↑
integration
    ↓
E2E
    ↓
staging
    ↓
canary
    ↓
production
```

理论上越往下，证据越接近我们真正关心的产品现实。

与此同时：

```text
cost ↑
risk ↑
diagnostic difficulty ↑
```

所以仍然是之前那套经济学，只不过扩展到了整个生命周期。

这也是一个很重要的原则：

> **越靠近真实产品的验证越有权威，但越不能承担大量探索。**

不要让生产环境告诉你：

```text
1 + 1 算错了
```

这种错误应该几毫秒就在本地发现。

Production 应该帮助发现那些只有真实环境才能暴露出来的问题。

---

而 production oracle 也远远不只是：

```text
HTTP 500 rate
```

我们可以再次按照“离产品语义的距离”分层。

最底层：

```text
Infrastructure

CPU
memory
disk
network
process alive
```

然后：

```text
System behavior

latency
error rate
throughput
queue depth
availability
```

再往上：

```text
Product behavior

checkout completion rate
search success
upload success
time-to-first-project
```

再往上：

```text
User outcome

用户有没有完成真正目标？
retention 有没有下降？
任务成功率有没有变化？
```

这和我们之前讲 Dashboard oracle 是同一个问题。

比如：

```text
server CPU normal ✓
HTTP error rate normal ✓
```

完全不能证明：

```text
checkout works
```

同样：

```text
checkout endpoint 200 ✓
```

也不能证明：

```text
用户真的能成功购买商品
```

因此 production observability 也存在：

> **Oracle quality problem。**

---

这里有一个我认为对 AI Coding 特别重要的变化。

传统 monitoring 经常是：

```text
Dashboard
↓
人偶尔看看
```

这对 autonomous iteration 不够。

AI 需要的是：

```text
machine-readable production feedback
```

例如明确：

```text
SLO:
checkout_success_rate >= 99.5%

guardrail:
p99_latency <= 800 ms

business invariant:
captured_payment_without_order == 0

rollout policy:
violate any critical guardrail
→ automatic rollback
```

现在生产环境第一次真正成为：

> **AI iteration loop 的一部分。**

不是：

```text
AI writes code
→ CI green
→ deploy
→ hope
```

而是：

```text
AI modifies
   ↓
pre-production assurance
   ↓
controlled exposure
   ↓
production evidence
   ↓
accept / rollback / diagnose
   ↓
AI modifies
```

---

而且这和我们前面讨论 regression test 的结论还能连接起来。

假设 production 出现：

```text
某种极特殊 request
→ checkout double charge
```

最弱的反馈循环是：

```text
production incident
→ 加一个 regression test
```

更好的还是：

```text
production counterexample
        ↓
发现缺失 specification
        ↓
例如：
∀ successful checkout:
captured_payment_count = 1
        ↓
加强 property / invariant
        ↓
pre-production test
+
production invariant monitoring
```

于是同一条产品知识同时存在于两个位置：

```text
Development:
prevent violation

Production:
detect real violation
```

这就是很强的互补证据。

---

现在我们也可以回答“哪些东西应该自动化”。

我不会给“能自动化就自动化”这种答案。

对 AI-driven iteration，一个检查特别值得自动化，当它：

```text
重复发生
+
结果可机器判断
+
反馈能够改变下一步决策
+
误判成本可接受
```

最后一点非常重要。

比如：

```text
type error
```

几乎可以完全自动处理。

而：

```text
这个新的 onboarding 是不是让人感觉更舒服？
```

如果 oracle 还不可靠，就不应该强行把一个模糊 LLM judge 伪装成绝对真理。

这里依然遵循我们第一课的原则：

> Oracle 的可信度决定 automation 能获得多大的决策权。

可以逐渐升级：

```text
observe only
      ↓
alert
      ↓
block merge
      ↓
block deploy
      ↓
automatic rollback
      ↓
AI automatically modify system
```

越往下，automation authority 越高。

相应地，oracle 必须越可靠。

这是一条非常重要的原则：

> **Automation authority should be proportional to evidence reliability.**

---

这样我们就自然走到接下来原本准备讨论的 **testability**，但现在可以给它一个更广的定义。

Testability 不只是：

> “这个 class 容不容易 unit test。”

对我们的目标，更好的定义是：

> **系统是否容易被外部实验、观察、控制和判断。**

它至少包含四个属性：

```text
Observability
能看到系统发生了什么

Controllability
能把系统置于需要验证的状态

Isolatability
能控制验证的边界和 blast radius

Reproducibility
同样条件下能可靠地重复实验
```

例如一个系统如果：

```text
无法构造某种用户状态
无法知道消息最终有没有处理
没有 correlation ID
依赖不可控的外部环境
无法 reset 数据
无法 replay request
```

那么即使业务代码写得再漂亮，它对于 AI continuous iteration 来说都是一个**低 testability 系统**。

这就是下一步很值得深入的地方：

> **如何把系统设计成一个“容易获得证据”的系统？**

从这里会自然进入 dependency、mock、test fixtures、environment、dependency injection、observability、determinism、replay、sandbox 等问题。

而我们不会把它们当成“为了写测试而加的技巧”，而是把 testability 看成一种直接影响 AI 迭代速度和可靠性的**架构属性**。