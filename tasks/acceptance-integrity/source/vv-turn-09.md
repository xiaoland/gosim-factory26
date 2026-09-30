# T09 | turn e3510a4d-a518-4f46-8286-452149fdc4ac | startedAt 1787847417.281462


## userMessage | message e3510a4d-a518-4f46-8286-452149fdc4ac


我基本都理解，也同意；唯独除了「一套关于“这个软件可能怎样坏掉”的编码知识」，而且我反感regression tests；难道不是，收拢系统“正确”的空间更好吗（大多数情况下）。

## agentMessage | message 5ec1bdf2-f978-43cc-b4e4-e8ed7393e168


对，我认为你的表述比我刚才那句更接近我们真正需要的模型。

“一套关于软件可能怎样坏掉的编码知识”更像传统测试文化里的视角；如果目标是让 AI 持续迭代系统，更理想的是：

> **尽可能刻画“允许的正确行为集合”，而不是不断积累“不允许出现的历史案例”。**

可以稍微形式化一下。

假设所有可能行为组成空间 \(B\)，真正满足产品要求的行为组成：

\[
C \subseteq B
\]

我们的 specification 真正想做的是逐渐逼近 \(C\)：

```text
所有可能行为 B
┌─────────────────────────────┐
│                             │
│       正确行为 C            │
│       ┌─────────────┐       │
│       │             │       │
│       └─────────────┘       │
│                             │
└─────────────────────────────┘
```

一个好的：

- invariant
- contract
- property
- state machine
- acceptance criterion
- performance constraint

实际上都在描述 \(C\) 的边界。

例如：

```text
每笔成功转账：
source.balance 减少 x
destination.balance 增加 x
总资金量不变
```

这比保存一个：

```text
曾经有一次 transfer(100) 把钱扣了两次
```

的 regression test 强得多。

因为后者只排除了一个点：

\[
b_1 \notin C
\]

而前者可能一次性排除一整类错误行为。

这就是你说的“收拢正确空间”。

而且我认为这个区别非常重要。

---

所以我会修正上一课的表达。

测试系统最好不是：

```text
Known bugs
   +
Known bugs
   +
Known bugs
   +
...
```

而应该尽量发展成：

```text
Product semantics
      ↓
properties / invariants / contracts
      ↓
越来越精确地限定 acceptable behavior
```

这是 **intensional specification**：

> 用规则描述什么是正确。

而大量 regression examples 更接近 **extensional specification**：

> 枚举一些正确/错误实例。

前者通常具有更强的泛化能力。

---

这也解释了你为什么可能会反感 regression tests。

例如曾经出了 bug：

```text
用户把用户名改成空字符串后系统 crash
```

最机械的处理方式是：

```python
def test_bug_381():
    update_username("")
    assert ...
```

然后系统里逐渐出现：

```text
test_bug_381
test_bug_427
test_bug_512
test_bug_693
...
```

这其实是一种 specification debt。

更好的处理应该先问：

> 这个 bug 揭示了哪个我们之前没有表达出来的规则？

可能真正缺失的是：

```text
username satisfies:
1 <= len(username) <= 50
```

那么应该增强：

```text
input contract
property tests
API validation
```

而不是仅仅永久保存那个 `" "` example。

也就是说：

```text
Bug
 ↓
寻找其所属的 failure class
 ↓
发现缺失的 property
 ↓
加强 specification
```

如果做到这一步，原来的 regression case 甚至可能没有继续独立存在的必要。

这一点我赞同你的倾向。

---

例如还有一个 bug：

```text
排序算法在 [2, 2, 1] 上丢失一个 2
```

最弱的修复：

```python
assert sort([2, 2, 1]) == [1, 2, 2]
```

更好的修复是意识到缺了一条 property：

\[
multiset(sort(x)) = multiset(x)
\]

于是：

```python
@given(...)
def test_sort_preserves_elements(xs):
    assert Counter(sort(xs)) == Counter(xs)
```

现在 `[2,2,1]` 只是帮助我们**发现 specification hole 的 counterexample**。

它不是最终知识。

最终知识是：

> sort 必须保持输入 multiset。

这个 distinction 很关键。

---

这甚至可以借用数学里的关系理解。

当某个测试发现：

\[
x \rightarrow failure
\]

它给我们的最好价值不是：

> 永远记住 x。

而是：

> 为什么 x 会失败？我们此前缺失了哪个更一般的约束？

然后寻找：

\[
P(x)
\]

并希望得到：

\[
\forall x,\;P(x)\Rightarrow Correct(x)
\]

当然软件工程里通常证明不了最后一步，但方向应该如此。

---

不过我不会完全删除 regression examples。

有三种情况下它仍然很有价值。

第一种是我们暂时不知道怎么泛化。

生产环境出现：

```text
Safari 17.3
+ OAuth redirect
+ third-party cookies disabled
```

才会触发问题。

我们可能暂时不知道更深层的 property。

这时候保留 counterexample 是理性的：

```text
先确保已知 failure 不回来
```

然后再慢慢抽象。

第二种是这个 example 本身就是重要产品场景。

例如：

```text
用户购买商品 → 支付成功 → 收到订单
```

这与其叫“regression test”，不如说是：

> permanent acceptance scenario。

即使它曾经发现 bug，也不应该因为我们找到了更一般 property 就删掉。

第三种是复杂系统存在难以表达的 emergent behavior。

很多 E2E failure 很难被一个漂亮 invariant 完整描述。

这时候 concrete scenarios 本身就是重要 evidence。

---

所以我会区分两个动作：

```text
Regression locking

发现 bug
→ 给这个具体 bug 加一个永久 test
```

和：

```text
Specification strengthening

发现 bug
→ 找到被遗漏的语义规则
→ 扩大 specification
→ 让整个 failure class 变得非法
```

我认为你的偏好实际上是第二个。

而对 AI-driven development，我也更推荐第二个。

因为如果主要依赖 regression locking：

```text
AI sees:
case 1
case 2
case 3
...
```

很容易演变成：

> 对测试集合做 patch。

而如果主要依赖：

```text
invariant
property
contract
state model
generated scenarios
```

AI 面对的是一个**行为边界**。

它必须在那个边界内寻找实现。

这是明显更健康的优化目标。

---

所以我们甚至可以把上一课的结论进一步修改成：

有限测试的主要目的不应该只是“积累失败案例”，而应该是帮助我们不断形成更好的 **behavioral model**：

```text
examples
boundaries
production failures
random generation
     │
     ↓
counterexamples
     │
     ↓
发现 specification gap
     │
     ↓
property / invariant / contract / model
     │
     ↓
收紧 acceptable behavior space
```

这样看，测试最有价值的产物有时甚至不是 test 本身，而是：

> **对“正确”更好的理解。**

而 regression example 是发现这一知识的一个 witness。

我认为这是一个值得保留到后面所有讨论里的修正：

> **Fault-oriented testing 用于探索哪里可能错；specification-oriented testing 用于定义什么才算对。对于 AI 持续迭代，后者应该是主体，前者是发现 specification 缺口的手段。**

这样的话，我们接下来讨论 unit / integration / E2E 时，也不应该从“哪里更容易发现 bug”出发，而应该从：

> **同一个正确性约束，在哪个观察边界上表达最自然、最稳定、成本最低？**

来推导测试分层。