# T07 | turn be36515f-2dcf-42f1-8c3e-40478284717a | startedAt 1787792381.675177


## userMessage | message be36515f-2dcf-42f1-8c3e-40478284717a


是的，承认实际上无法做到绝对保证——只要最上层还是人的自然语言意图，就永远存在解释空间很重要，而且自然语言和人脑袋里的思想也无法保证一致。我觉得你现在给出的解决方案就足够了。
那我们现在离开这个小分支，回到主线上？还是说你计划继续深入这个分支，直到该模型可用？

## agentMessage | message 36d10e24-a906-4e1e-b272-13d7cbc0174f


我建议现在回主线。

这个分支已经到了“足够可用”的程度，再继续深入很容易滑向 requirements engineering、formal specification、refinement calculus 这些本身就可以单独学很久的领域，而目前它们不是我们的主要目标。

我们现在已经拿到了一个足够实用的工作模型：

```text
Product intent
    ↓
Behavioral property
    ↓
Observable evidence
    ↓
Oracle
```

并且知道每次转换都可能发生 semantic drift，因此用三个手段控制它：

```text
1. 明确哪些变化是 product-relevant，
   哪些只是 implementation detail

2. 检查 oracle：
   semantic change → 应该失败
   semantic-preserving change → 不应该失败

3. 必要时通过 semantic mutation
   验证测试是否真的能捕获需求破坏
```

到这里，这个模型已经能实际指导测试设计了。以后碰到问题，我们再回来加深，而不是现在把它完善成一套形式化理论。

主线下一步其实出现了一个很自然的问题。

刚才解决的是：

> **给定一次软件行为，我们怎么判断它对不对？**

也就是 Oracle 问题。

但即使 oracle 完美，还存在另一个完全独立的问题：

> **我们应该让软件经历哪些情况？**

比如：

```python
divide(10, 2) == 5
```

oracle 没问题。

但我们只测试：

```text
10 / 2
```

显然仍然远远不能说明 `divide` 可靠。

所以自动化测试至少有两个正交问题：

```text
                 Testing
                    │
          ┌─────────┴─────────┐
          │                   │
     Test Oracle          Test Input
    怎么判断对错？       测哪些情况？
```

前一个我们刚刚讨论过。

后一个会把我们带入软件测试真正的核心理论之一：**test case design / test selection**。

也就是：

> 软件的输入空间通常近乎无限，我们为什么有理由认为测试这有限的几十、几百、几千个 case 就有价值？

这里会自然出现：

- equivalence partitioning
- boundary value analysis
- decision tables
- state-transition testing
- combinatorial testing
- property-based testing
- coverage，以及“coverage 到底证明了什么、没证明什么”
- risk-based testing

而且这跟 AI 持续迭代直接相关：AI 不只需要一个会说 PASS/FAIL 的 oracle，它还需要一个足够强的 **challenge set**。否则它完全可能对已有测试过拟合。

所以我会把下一课定成：

> **有限的测试集，为什么能为近乎无限的软件行为提供有意义的证据？**

这正好回到 Software Testing 的主线上。