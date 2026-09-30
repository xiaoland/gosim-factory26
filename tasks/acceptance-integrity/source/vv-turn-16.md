# T16 | turn dced19ae-c245-4d22-9165-3c51902db535 | startedAt 1788279872.871596


## userMessage | message dced19ae-c245-4d22-9165-3c51902db535


这解答了我长期以来觉得TDD方向正确，但实践起来不行的这种错位；特别是`mock_repository.save.assert_called_once_with(...)`抓得很好，找到了根本问题；你给出的TDD SOP也十分准确好用。
而且这样的话，我就终于可以看到优化方案->实现->验收这样一个粒度过粗、反馈过慢的 task workflow的希望了。这应该正要依赖我们接下来要讨论的问题，所以我们继续。

## agentMessage | message 763b652f-af99-4bb5-a009-7713af5074e3


对。现在正好可以回答这个“为什么 TDD 有时真的会 drive design”。

关键机制不是“测试 magically 产生好架构”，而是：

> 当你要求一个行为能够被便宜、稳定、独立地验证时，系统会受到一组设计压力。

如果测试表达的是稳定的产品/领域语义，这些压力通常有益；如果测试表达的是实现过程，这些压力就可能把设计带偏。

先看前一种。

假设需求是：

```text
“下单时，库存不足不能扣款；
库存足够且付款成功后订单才成立。”
```

如果代码一开始写成：

```text
HTTP handler
  ├─ 查数据库
  ├─ 判断库存
  ├─ 调 Stripe
  ├─ 写订单
  ├─ 发消息
  └─ 返回 response
```

想验证“库存不足不能扣款”，你会发现自己不得不启动数据库、HTTP、支付系统，甚至消息队列。

测试在告诉你：

> 这个业务判断和太多副作用缠在了一起。

于是一个自然的设计动作是把“决定应该发生什么”与“真正执行副作用”分开：

```text
Order decision
    ↓
需要：
- reserve inventory
- capture payment
- create order

Effect execution
    ↓
DB / payment / queue
```

甚至核心决策可以接近：

```python
decision = decide_checkout(cart, inventory, payment_state)
```

然后非常便宜地验证：

```text
库存不足
→ decision 不包含 CapturePayment
```

测试并没有告诉你“应该使用某个 class hierarchy”。

它只是施加了一个压力：

> **这个重要 property 应该能在不拖着整个世界一起运行的情况下被观察。**

于是 design 逐渐产生 separation of concerns。

这就是好的 “tests drive design”。

---

这种设计压力大致会反复推导出几类性质。

第一类是 **显式状态，而不是隐藏状态**。

难测试的代码经常是：

```text
global config
singleton
current time
environment variable
implicit current user
```

测试迫使你问：

> 这个行为真正依赖什么？

于是：

```text
隐式 dependency
→ 显式 input / dependency
```

结果不仅更容易测试，也更容易理解和推理。

第二类是 **decision 与 effect 分离**。

```text
计算“应该做什么”
```

通常可以做得快、确定、密集验证。

```text
真正做这些事情
```

再用 integration evidence 验证。

这就是很多人称为 Functional Core / Imperative Shell 的思想，但名称不重要，机制重要：

> 把需要大量推理的地方尽量放到便宜的验证边界里。

第三类是 **明确的 contract boundary**。

例如应用真正依赖的可能并不是：

```text
Stripe SDK
```

而是：

```text
capture(amount, payment_method)
→ Captured | Declined | Unknown
```

一旦你能够明确说出这个 contract，说明设计本身变清楚了。

注意这不意味着：

> 每个东西都创建 InterfaceFactoryManager。

只有在一个 boundary 确实有独立语义、独立不确定性的时候，抽出来才有意义。

第四类是 **stable semantic interface**。

如果你的测试总要写：

```text
obj.a.b.c[2].state
```

通常是在告诉你：

> 外部只能通过实现结构观察系统。

更好的设计可能让重要语义直接存在：

```text
order.is_confirmed
payment.status
workspace.owner
```

这同时提高：

```text
testability
observability
debuggability
AI readability
```

---

现在就能理解为什么 mock-heavy TDD 会 drive 出另一套截然不同的设计。

假设测试是：

```python
mock_inventory.expect("reserve").once()
mock_payment.expect("capture").once()
mock_repo.expect("save").once()
mock_mail.expect("send").once()
```

为了让这种测试容易写，你会自然设计出大量：

```text
object
→ collaborator
→ collaborator
→ collaborator
```

然后测试验证：

```text
谁调用谁
调用几次
调用顺序
传什么参数
```

结果 architecture 会被 interaction graph 驱动。

这并非一定错误——有些 protocol 本身就关心 interaction。

但如果产品只关心：

> “订单最终成立且只扣一次款。”

那么这些 tests 就给系统加入了大量不必要约束。

于是：

```text
重构 implementation
```

变成：

```text
修改 implementation
+
修改一大片 mocks
```

你之前感觉 TDD “方向正确但实践不行”，很可能就是因为：

> **正确的是 specification-first 的反馈循环；有问题的是把 interaction specification 当成 behavioral specification。**

这两者被长期混在了“TDD”这个名字下面。

---

这里还有一个很实用的设计判断：

当一个测试很难写时，不要马上得出：

> “这个代码设计得不好。”

先问：

> **这个 property 本来就应该在这个边界验证吗？**

例如：

```text
OAuth redirect 真正能在 Safari 工作
```

本来就是高层 integration/E2E property。

为了把它“变得 unit-testable”而抽象掉浏览器和 OAuth provider，反而把真正语义抽没了。

所以正确的 testability 不是：

> everything should be easy to unit test。

而是：

> **每个重要 property 都应该有一个成本与其语义相匹配的验证边界。**

这是个重要约束，否则“Design for Testability”也会异化。

---

这就直接连接到你说的 workflow 粒度问题。

原来的 AI task 很可能是：

```text
优化 checkout
    ↓
AI 修改很多代码
    ↓
跑完整测试
    ↓
E2E
    ↓
发现失败
```

反馈极慢，而且失败空间巨大。

更好的工作单位不是 “feature implementation”，而是 **behavioral slice**。

比如：

```text
目标：
减少 checkout latency，
但保持 payment correctness。
```

不要直接变成一个巨大 task。

可以逐步变成：

```text
1. 建立/确认关键约束
   - payment 至多 capture 一次
   - failed inventory 不 capture
   - successful checkout 创建 exactly one order

2. 找到最小有效验证边界

3. 先优化一个局部瓶颈

4. 跑局部 property / integration evidence

5. 下一小步

6. 若干小步后跑一次 product-level acceptance

7. 最后跑 performance / production-like evaluation
```

于是闭环从：

```text
方案
────────── 很长实现 ──────────
验收
```

变成：

```text
方案
 ↓
property
 ↓
小实现
 ↓
快速 evidence
 ↓
小实现
 ↓
快速 evidence
 ↓
integration evidence
 ↓
继续
 ↓
E2E acceptance
```

这就是 TDD 在 AI Coding 里真正可能产生的杠杆：

> **把一次大的搜索问题分解成许多受到局部正确性约束的小搜索问题。**

AI 每一步需要探索的 solution space 都更小，而且反馈更快。

---

但还有一个关键点：不要让局部循环取代最终验收。

因为：

```text
所有局部 properties ✓
```

并不推出：

```text
产品 requirement ✓
```

所以比较合理的是双时间尺度：

```text
Fast loop
─────────
property
unit/component
focused integration
每个小修改运行

Slow loop
─────────
critical E2E
performance
realistic environment
完成一个 behavioral slice 后运行
```

Fast loop 负责：

> 搜索和诊断。

Slow loop 负责：

> 防止局部优化偏离产品。

这跟优化算法里的 local objective / global objective 很像。

而 AI 特别需要 global check，因为它非常容易找到满足局部 objective 的奇怪解。

---

所以如果现在给我们此前所有讨论加上一条很实际的 AI 开发 SOP，我会先只加这一条，不急着发明更大的流程：

```text
不要把“实现一个 feature”作为最小迭代单元。

优先寻找：
一个稳定的 behavioral property
+
一个足够小的实现变化
+
一个快速可信的反馈边界。
```

然后周期性回到：

```text
更高层 integration / E2E / production-like evidence
```

检查这些局部正确有没有组合成真正的产品正确。

这应该就是你刚才所说，从“优化方案 → 实现 → 验收”这种粗粒度流程里出来的第一条实际路径。

而再往下一步，就会遇到一个非常现实的问题：

> **一个 feature/改动应该怎样被切成 behavioral slices，才能既足够小，又不把产品语义切碎？**

我认为这个问题比继续讨论 TDD 流派更值得深入，因为它直接决定 AI Coding 的 task granularity 和反馈速度。