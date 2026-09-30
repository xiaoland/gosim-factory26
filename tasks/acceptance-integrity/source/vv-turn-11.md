# T11 | turn fe7b3fbe-7bcb-471a-89d4-caf1261850ee | startedAt 1787915505.711057


## userMessage | message fe7b3fbe-7bcb-471a-89d4-caf1261850ee


我对mock也是尤其的反感，你说的「如果世界和我想象的一样，我的代码能工作」某种程度上解答了我为什么反感，但我认为还有更深层次的原因：我想象的世界会变化，而且是因为产品需求变化而变化，总的来说，我感觉mock本身是脆弱的。（只是一些随想）
相对的，我很喜欢E2E，我猜，是因为它测试很好地让测试不依赖具体的实现，而具体实现的变化是很快的，脆弱的我，AI也喜欢作弊的。
总的来说，我理解了这个测试分层的原理，也认同，而且这应该已经够用。
而且我还特别喜欢这里面「形成互补证据」这点，这样，测试分层就不只是切分，它们的组合可以创造“利润”，实现杠杆。
而且我也同意还看看测试成本的组成，否则我们就缺少了一把分层的“尺子”

## agentMessage | message 3d259d97-6b1d-401d-83a2-0832d0f5eec8


对，你对 mock 的反感可以再往下抽象一层：它的问题不只是“和真实世界不一样”，而是它经常制造了一个需要额外维护的“影子世界”。

真实 contract 是：

```text
Application ↔ Database / API / Service
```

mock 之后变成：

```text
Application ↔ 我们想象中的 Database / API / Service
```

于是系统中实际上出现了两份知识：

```text
真实 dependency 的行为
mock 对 dependency 行为的描述
```

两者必须长期同步。产品需求、接口语义、错误模式一变化，就可能产生 drift。

这也是 mock 脆弱性的一个更本质来源：

> **Mock 把外部世界的 specification 复制进了测试。**

如果复制出来的 specification 本身就是你真正想验证的东西，那当然有意义；但很多时候，我们真正想知道的恰恰是：

> “真实世界是不是仍然满足我的假设？”

这时 mock 会把最需要验证的不确定性直接假定掉。

所以我会把 mock 当成一种很具体的工具，而不是默认测试方式：

> 当真实 dependency 的成本高到不能接受，并且它的 contract 足够稳定、足够明确时，用 test double 换取速度。

而不是“unit test 就应该 mock dependency”。

这也解释了你为什么天然偏爱 E2E：它的一个巨大优点是 **semantic coupling 高、implementation coupling 低**。只要测试写在正确的产品语义上，实现可以大幅重写，测试仍然成立。这对于 AI 尤其重要，因为我们希望约束的是：

```text
你必须达到这个结果
```

而不是：

```text
你必须用我预想的过程达到这个结果
```

否则 AI 很容易变成“满足测试代码”，而不是“满足产品”。

---

现在进入你说的“尺子”。

我认为测试成本至少要拆成六种，而不能只看 runtime。

### 1. Execution cost：运行成本

最显眼：

```text
CPU / memory
第三方 API
browser
database
部署环境
运行时间
```

比如：

```text
unit      5 ms
integration 500 ms
E2E       20 s
load test 15 min
```

这是最容易量化的一项，但往往不是最大的成本。

---

### 2. Feedback latency：反馈延迟

这里和 execution time 有区别。

一个测试即使只跑 2 分钟，如果必须：

```text
build
→ deploy
→ provision environment
→ seed data
→ execute
→ collect result
```

AI 可能 8 分钟以后才能得到反馈。

对于持续迭代：

> **feedback latency 是一等公民。**

因为闭环效率大约是：

```text
修改
→ feedback
→ 修改
→ feedback
```

反馈从 10 秒变成 10 分钟，不只是贵了 60 倍，而是直接改变 AI 能进行多少轮搜索。

---

### 3. Maintenance cost：维护成本

这是你刚才讨论 mock 时最重要的一项。

问：

> 产品正常演进，但正确行为没有被破坏时，这个测试需要多频繁修改？

例如：

```text
assert button.children[2].text == "Submit"
```

maintenance cost 极高。

而：

```text
user_can_submit_order()
```

可能低很多。

所以我们可以把这种成本理解为：

> **测试与 incidental implementation detail 的 coupling。**

这也是为什么一个运行昂贵但语义稳定的 E2E，有时反而比一堆 mocked unit tests 更便宜。

不能只看单次执行时间。

---

### 4. Diagnostic cost：失败诊断成本

测试失败以后：

> 我们获得了多少 information？

例如：

```text
property test:
total_balance invariant violated
```

信息非常强。

而：

```text
E2E:
checkout failed
```

可能需要翻：

```text
browser logs
network traces
backend logs
database
queue
payment service
```

所以测试的价值不只是“能否发现错误”，还包括：

> **能否缩小错误空间。**

这也是前面“互补证据”的真正杠杆所在。

假设：

```text
domain property ✓
DB integration ✓
payment integration ✓
checkout E2E ✗
```

这四个结果组合起来，比单独一个 E2E failure 信息量大得多。

测试分层因此可以理解成一种 **diagnostic decomposition**。

---

### 5. Reliability cost：测试本身不可靠的成本

也就是：

```text
flakiness
false positive
false negative
environment noise
timing sensitivity
```

这是很危险的一项。

假设一个测试 2% 的概率随机失败。

如果 suite 有 100 个这种测试：

\[
P(\text{至少一个随机失败})
=1-0.98^{100}
\approx 87\%
\]

这时候整个 suite 基本失去作为 AI oracle 的资格。

对于人类开发者，flaky test 是烦人。

对于 autonomous AI，它更加危险，因为：

```text
随机失败
→ AI 认为代码有问题
→ 修改正确代码
→ 引入真正的问题
```

所以 AI iteration 对 test determinism 的要求实际上更高。

---

### 6. Semantic cost：错误约束系统的成本

我认为这是最容易被忽略、但可能最昂贵的成本。

测试本身可能写错。

比如：

```text
产品 requirement:
用户能够找到自己的项目
```

测试：

```text
URL == "/projects"
```

现在 AI 想把产品改成：

```text
/workspace
```

产品行为完全正确，但测试拒绝变化。

于是测试从：

> safety net

变成：

> architecture prison。

这就是 specification coupling 的成本。

对于 AI 特别明显，因为 AI 有能力大规模重构。如果测试把大量历史实现选择固化，它就会人为限制 solution space。

所以我甚至会说：

> **一个坏测试不只是没有价值；它具有负价值。**

---

到这里，我们就可以定义一个相当实用的测试经济模型。

对于一个测试 \(T\)，不要问：

> 它是 unit 还是 E2E？

先问：

```text
Evidence(T)
────────────────────────────────
Execution cost
+ Feedback latency
+ Maintenance
+ Diagnosis
+ Flakiness
+ Semantic coupling
```

当然这不是要求真的计算一个数字，而是一种决策框架。

更重要的是你刚才提到的“组合创造利润”。

测试 suite 的价值不能简单写成：

\[
Value(A+B)=Value(A)+Value(B)
\]

因为会存在两种效应。

一种是重复：

```text
A 和 B 基本证明同一件事情
```

那么边际价值很低。

另一种是互补：

```text
A 验证 domain property
B 验证真实 database contract
C 验证 product workflow
```

组合后：

```text
A ✓
B ✓
C ✗
```

本身就是新的诊断信息。

因此理想的 test portfolio 应该追求：

> **low evidence overlap + high diagnostic complementarity。**

这比 Test Pyramid 的“70% unit、20% integration、10% E2E”有用得多。

---

所以现在我们已经有一把还不错的“尺子”：

一个测试值得存在，当它同时满足：

```text
1. 提供某种其他测试不能廉价提供的证据

2. 与产品语义的 coupling 高
   与具体实现的 coupling 低

3. 生命周期成本与证据价值相称

4. 与其他测试组合后，
   能增加故障定位或可信度
```

这里其实也能解释你喜欢 E2E、讨厌 mock 的直觉：你优先看重的是 **semantic durability**，而不仅仅是 execution speed。

这个偏好本身没有问题。真正需要防止的是走到另一个极端——所有东西都靠 E2E。因为 E2E 虽然 semantic durability 很可能很好，但 diagnostic cost 和 feedback latency 通常较高。

理想状态不是“多写 unit”或者“多写 E2E”，而是：

> **用少量高语义保真的 E2E 锚定产品正确空间，再用便宜的 property / integration tests 对这个空间进行高密度约束和快速诊断。**

我认为这已经足够作为后面实际设计 test suite 的经济学基础了。下一步主线就可以开始讨论：**哪些测试应该自动化、什么时候自动化，以及 testability 为什么实际上是一种系统架构属性。**