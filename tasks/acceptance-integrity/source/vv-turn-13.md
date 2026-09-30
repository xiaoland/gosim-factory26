# T13 | turn f1b7255d-aaee-4251-9a95-fdd3c99224b6 | startedAt 1788242392.253296


## userMessage | message f1b7255d-aaee-4251-9a95-fdd3c99224b6


同意。而且你对这个目标的重新定义抓到了问题的本质。然后我们确实已经把框架搭建好了，要向落地前进一步。

## agentMessage | message d9325786-8a9b-4217-bef1-67acc335922e


那就把 “testability” 从概念变成工程设计原则。我们现在真正关心的是：

> 怎样设计一个系统，使 AI 可以低成本地设置条件、运行真实行为、获得可信证据、定位失败，然后再次迭代？

我会把它叫作 **Design for Assurance**。

先从一个最实用的模型开始。一个系统容易验证，需要四件事同时成立：

```text
Control      能设置实验条件
Execute      能运行目标行为
Observe      能取得有意义的结果
Reset        能可靠地再次实验
```

也就是：

```text
Setup
  ↓
Exercise system
  ↓
Collect evidence
  ↓
Judge
  ↓
Reset
  ↺
```

如果这四步中的任何一步很困难，AI 的迭代闭环都会变慢。

---

先看 Control。

假设你要验证：

> 用户 session 过期后，保存操作应该要求重新认证，但不能丢掉用户正在编辑的数据。

一个低-testability 系统可能要求：

```text
真的登录
↓
等 24 小时
↓
session 自然过期
↓
再操作
```

这显然不能迭代。

真正的问题不是“测试怎么写”，而是系统没有给我们控制时间的能力。

好的设计可能允许：

```python
app = create_app(
    clock=TestClock("2026-09-01T10:00:00")
)
```

于是：

```python
login(user)

clock.advance(hours=25)

save_document()
```

这里 `clock` 并不是因为“我要 mock Date.now()”。

它代表一个更一般的原则：

> **凡是影响系统行为、但实验者无法可靠控制的东西，都会降低 testability。**

常见的不可控变量包括：

```text
time
randomness
network
external services
process scheduling
filesystem
environment variables
identity
database state
feature flags
```

设计时应该问：

> 哪些变量未来需要人为构造？

这就是 controllability。

---

第二个是 Observe。

这是很多系统真正糟糕的地方。

例如 AI 做了：

```text
POST /send-invoice
→ 200 OK
```

测试通过了吗？

不知道。

真正发生的可能是：

```text
request accepted
↓
message queued
↓
worker crashed
↓
invoice never sent
```

所以 `HTTP 200` 只是非常浅的 observable。

你真正需要观察的是产品语义：

```text
invoice eventually delivered
```

于是系统可能需要暴露：

```text
job state
event log
delivery status
correlation ID
domain event
database state
```

注意，我这里不是说：

> 为测试暴露内部实现。

而是：

> **让系统的重要事实具有可观察的 representation。**

例如：

```text
InvoiceRequested
InvoiceGenerated
InvoiceDeliverySucceeded
```

这种 domain-level event 不只是为了测试。

它同时服务于：

```text
debugging
observability
audit
production monitoring
AI diagnosis
```

这就是好的 testability 经常和好的 production observability 是同一个设计。

---

第三个是 Reset。

这个问题在 E2E 和 AI iteration 中特别关键。

假设每次测试：

```text
create user
create workspace
create project
run operation
```

然后下一轮测试继续使用同一个 staging database。

很快就会出现：

```text
name already exists
quota exceeded
previous run left state
another test changed permissions
```

于是：

```text
same test
same code
different result
```

AI 几乎无法判断发生了什么。

所以一个适合 autonomous iteration 的系统需要非常强的：

> **state lifecycle management。**

常见方案：

```text
ephemeral database
transaction rollback
namespace-per-test
temporary filesystem
container-per-suite
unique tenant
fixture snapshot
environment recreation
```

核心不是哪种技术，而是：

> 一次实验产生的状态不能污染下一次实验。

这其实就是我们之前谈 flakiness 的根源之一。

---

这里我想特别处理一下 mock，因为它现在可以放到正确的位置上了。

我们刚才说：

```text
external dependency
↓
难以控制
```

一种办法是 mock。

但不是唯一办法。

更好的思考顺序应该是：

```text
我能否使用真实 dependency？
        ↓ no
能否使用 lightweight real implementation？
        ↓ no
能否使用 local emulator / container？
        ↓ no
能否使用 contract-tested fake？
        ↓ no
最后才考虑 interaction mock
```

例如数据库：

```text
mock Repository
```

和：

```text
real Postgres in container
```

今天两者运行成本的差距已经不像十几年前那么巨大。

但是 evidence 差距非常大。

containerized Postgres 能真正告诉你：

```text
SQL 对不对
constraint 对不对
transaction 对不对
migration 对不对
serialization 对不对
```

mock repository 都假设这些东西已经正确。

所以一个很实用的原则是：

> **Prefer cheap reality over elaborate simulation.**

如果真实东西已经足够便宜，就不要构造一个影子世界。

这与你之前对 mock 的直觉是一致的。

---

但这里需要防止另一个极端。

假设 Stripe API 每次测试都真的扣款。

显然不合理。

所以 testability 很重要的一部分是设计一个**稳定 boundary**：

```text
Our system
    │
    │ PaymentPort
    ▼
Payment provider
```

我们的 domain logic 可以真正运行。

boundary 外：

```text
production → Stripe
test       → Stripe sandbox / contract-valid fake
```

这里 fake 的目标不是：

> 模拟 Stripe 的内部实现。

而是：

> 实现我们明确依赖的最小 contract。

区别很大。

例如不要写：

```python
mock.expect("createPaymentIntent").called_once()
```

而更像：

```python
payment = FakePaymentProvider()

checkout()

assert payment.captured_amount(order.id) == 100
```

前者验证过程。

后者验证 observable outcome。

即使使用 test double，我们依然保持 specification-oriented。

---

第四个问题是 Reproducibility。

有些 failure 的难点不是没发现，而是：

> 发现以后再也跑不出来。

AI 特别需要 reproducibility，因为它需要：

```text
failure
→ hypothesis
→ modification
→ rerun same experiment
```

所以应该尽可能记录：

```text
input
seed
system version
config
feature flags
dependency versions
environment
time
relevant state
```

property-based testing 很典型。

如果随机生成：

```text
[431, -5, 0, 431, ...]
```

发现 bug，就必须能输出：

```text
seed = 728194
```

然后：

```text
replay(seed=728194)
```

生产系统也类似。

一个成熟的系统最终很希望能够做到：

```text
production failure
       ↓
capture request / trace / state
       ↓
sanitized replay
       ↓
local or staging reproduction
```

这对于 AI 修 bug 会非常强。

---

于是我们可以开始形成一些非常具体的架构倾向。

一个 AI-friendly、assurance-friendly 的系统，我会倾向于：

```text
显式 domain boundaries
显式 contracts
可替换 external boundary
可控制 clock/randomness
结构化 domain events
稳定 correlation IDs
可快速构造 state
可快速清理 state
真实 dependency 尽可能 containerized
production traces 可 replay
关键 properties 机器可观察
```

你会注意到：

这些不是 testing framework 技巧。

它们已经是 architecture。

---

这里还有一个概念我觉得尤其适合我们的目标：

> **Evidence Surface**

也就是：

> 系统主动提供多少“可以判断它是否正确”的表面？

例如一个异步任务系统，如果只有：

```text
POST /job → 202
```

evidence surface 很弱。

如果还有：

```text
GET /job/{id}

{
  state,
  started_at,
  completed_at,
  result,
  failure_reason
}
```

再加：

```text
JobCreated
JobStarted
JobSucceeded
JobFailed
```

你的 evidence surface 就强很多。

AI 不再需要猜：

> “这个任务大概完成了吗？”

它可以直接查询。

这会大幅降低 oracle 成本、diagnostic cost 和 production debugging cost。

---

同理，一个很好的设计原则是：

> **重要 product state 应该尽量具有 stable semantic observables。**

比如 workspace 产品：

不要让测试只能知道：

```text
DOM 有一个 div
```

尽量让它能够知道：

```text
workspace exists
current user owns it
project count = 3
user can create project
```

UI E2E 再负责证明：

> 用户通过真实 UI 确实可以触达这些能力。

于是形成互补：

```text
Domain/API evidence
→ 系统状态确实正确

Browser evidence
→ 用户确实可以完成产品行为

Production evidence
→ 真实用户环境仍然成立
```

又回到了我们非常喜欢的 **complementary evidence**。

---

如果把这一课压缩成一个实际设计 checklist，我现在会让 AI 在设计 feature 时先问：

```text
1. 这个 feature 的关键 property 是什么？

2. 为验证它，我需要控制哪些条件？

3. 我需要观察哪些结果？

4. 状态怎样快速构造和 reset？

5. 哪些真实 dependency 可以直接使用？

6. 哪些 boundary 必须替代？
   替代品依据什么 contract？

7. 失败以后有没有足够信息定位？

8. production 中同样的 property 能否被观察？

9. production failure 能否被 replay？
```

如果一个 feature 在实现之前就回答了这些问题，后面的 automated assurance 成本通常会低很多。

所以你之前说验证已经向设计阶段蔓延，其实现在可以更进一步：

> **Testability 不是代码写完之后“方便测试”的属性，而是系统能否被持续验证、持续实验、持续改进的架构能力。**

而对于 AI Coding，它甚至直接决定：

> AI 每小时能进行多少次可靠的“假设 → 修改 → 验证”循环。

下一步我认为就可以从架构再次往实际流程推进：**一次 feature 从 requirement 到 production，究竟应该怎样建立它的 assurance plan。**

也就是不再分别讲 unit、E2E、observability，而是拿一个 feature，把我们目前所有理论真正组合成一次完整的软件迭代流程。