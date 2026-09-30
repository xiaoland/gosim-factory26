# T15 | turn 8f89d96b-027c-4e4b-a85b-3422d2c9825a | startedAt 1788279170.031346


## userMessage | message 8f89d96b-027c-4e4b-a85b-3422d2c9825a


没错。而且你这个方向判断很对，我们继续。

## agentMessage | message c76466bb-6e64-46b8-8b1a-deefdc56efca


那我们用目前已经建立的模型重新看 TDD，而不是从 Red-Green-Refactor 的口诀开始。

我认为 TDD 最值得保留的本质是：

> **在实现之前，先把下一小块“正确行为空间”表达成一个能够产生反馈的约束，然后让实现去满足它。**

所以它首先是一种“开发顺序”的选择。

普通开发很容易变成：

```text
想到需求
→ 写实现
→ 看起来差不多
→ 再写测试描述现有实现
```

这里存在一个很大的认知风险：测试是在实现之后产生的，所以我们很容易不自觉地把：

> “我写出来的东西”

合理化成：

> “本来就应该这样”。

TDD 把顺序倒过来：

```text
理解一小块期望行为
        ↓
形成 executable constraint
        ↓
确认它目前不成立
        ↓
寻找一个满足它的实现
        ↓
在约束不变的情况下改善实现
```

这就是 Red-Green-Refactor 为什么可能有价值。

其中我觉得 **Red 才是最容易被低估的一步**。

假设你直接写：

```python
assert transfer_preserves_total_balance()
```

然后它一开始就是 green。

你其实不知道：

> 这个 oracle 到底有没有能力区分正确和错误系统？

Red 的意义不是仪式，而是在提供一种非常便宜的证据：

> **我刚刚增加的 specification 对当前缺失的行为是敏感的。**

换句话说，Red 是在测试测试本身的 discriminating power。

这与我们之前谈 semantic mutation 是同一类思想，只不过是一个非常局部、非常便宜的版本。

---

Green 也常常被误解成：

> “赶紧写一个丑 implementation。”

更准确应该是：

> **找到一个 witness，证明当前这组约束至少是 satisfiable 的。**

比如你定义：

```text
∀ successful transfer:
source decreases by amount
destination increases by amount
total money unchanged
```

Green 就是在寻找一个实现 \(I\)，使：

```text
Specification(I) = true
```

这里测试扮演的不是“检查代码”的角色，而是在定义一个 solution space：

```text
所有可能 implementation

┌──────────────────────────────┐
│          不合法              │
│      ┌──────────────┐        │
│      │ 满足 tests   │        │
│      │ 的实现空间   │        │
│      └──────────────┘        │
│                              │
└──────────────────────────────┘
```

AI 或人类都可以在里面搜索。

这就来到 Refactor。

它其实可以被重新解释为：

> **保持 behavioral constraints 不变，在 implementation space 中继续搜索更好的点。**

比如：

```text
Implementation A
正确，但慢、复杂

↓ refactor

Implementation B
仍然满足相同 properties
但更简单、更快、更容易维护
```

因此 tests 给 refactoring 提供的是一个相对稳定的边界：

```text
这些可以改
这些行为不能改
```

这对 AI Coding 特别重要。

因为 AI 非常擅长大规模改变实现，而我们最需要告诉它的是：

> solution space 的边界在哪里。

---

但这样一解释，也马上能看到 TDD 的一个根本风险。

如果你测试写的是：

```python
mock_repository.save.assert_called_once_with(...)
```

那么你定义的 solution space 就变成：

```text
必须以我预想的方式
调用我预想的 collaborator
```

你其实不是在约束产品行为。

你是在约束 implementation trajectory。

所以：

> **TDD 的价值完全取决于先写下来的到底是什么。**

如果先写的是 stable semantic property，TDD 可以保护你。

如果先写的是当前脑中想象的 class interaction，TDD 反而会提前冻结架构。

这可能也是为什么有些人体验到：

> “TDD 让设计越来越好”

而另外一些人体验到：

> “TDD 让我维护一大堆 mock，而且不敢重构。”

两者完全可能都是真实经验。

---

因此我不会把：

> test-first

当成无条件正确的原则。

它有一个很重要的前提：

> **你对当前这一小块 specification 已经比对 implementation 更有把握。**

比如：

```text
转账保持资金守恒
用户名不能为空
parser round-trip 后语义不变
权限系统不能越权
```

很适合。

因为我们大致知道“对”是什么。

但假设正在探索一个新的 onboarding：

```text
用户怎样完成第一次项目创建才自然？
```

你甚至还不知道产品行为应该长什么样。

这时候先固化：

```text
点击 Button A
→ 出现 Modal B
→ 点击 Step C
```

很可能只是把一个尚未理解清楚的设计偶然选择写成 executable prison。

这种情况下更合理的是：

```text
探索
→ prototype
→ 用户/产品反馈
→ 逐渐发现稳定 requirement
→ 再把稳定部分 executable
```

所以 TDD 不是 discovery 的替代品。

它更适合：

> **已经形成一定理解之后，对 implementation 进行受约束搜索。**

---

这也给出了一个我认为很实用的判断：

如果你现在主要不知道：

> “怎么实现？”

TDD 很可能有帮助。

如果你主要不知道：

> “到底应该做什么？”

先写测试未必有帮助。

这两个不确定性不要混在一起：

```text
Product uncertainty
“什么才是好产品？”

Implementation uncertainty
“怎样可靠实现已知行为？”
```

TDD 主要压缩的是第二种。

---

再看 bug fix，就能连接我们之前关于 regression test 的讨论。

经典 TDD 会说：

```text
发现 bug
→ 写 failing test
→ 修复
→ test 永久保留
```

我们已经知道最后一步未必最好。

更好的版本可以是：

```text
production counterexample
        ↓
写 failing example
        ↓
确认能够 reproduce
        ↓
寻找遗漏的 general property
        ↓
让 property test fail
        ↓
修复
        ↓
保留 general property
```

具体 regression example 可以根据价值决定是否保留。

所以 failing example 在这里可以只是：

> **帮助发现 specification hole 的脚手架。**

不一定是永久资产。

这让我觉得你之前反感 regression test，其实并不和 TDD 的核心冲突。

---

现在进入 AI Coding。

AI 时代有一个很有意思的变化：

以前：

```text
写 implementation
```

很贵。

所以人会担心：

> “先写这些 tests 会不会降低我的开发速度？”

现在 implementation 的边际成本下降得非常快。

于是相对而言：

```text
清楚定义约束
构造 oracle
获得可靠反馈
```

的价值上升。

所以 TDD 的精神反而可能更重要。

但传统 TDD 的具体形式未必照搬。

因为 AI 有一个人类开发者没那么严重的问题：

> **它非常擅长对 visible tests 过拟合。**

比如你给它：

```python
assert foo(1) == 2
assert foo(2) == 4
assert foo(3) == 6
```

它完全可能写：

```python
return {1: 2, 2: 4, 3: 6}[x]
```

测试全绿。

所以 AI 时代更应该偏向：

```text
properties
invariants
generated inputs
真实 integration
少量 semantic E2E
independent acceptance evidence
```

而不是大量 enumerated examples。

也就是说，我们可以把 AI 时代的 TDD 改写成：

```text
先强化 behavioral specification
        ↓
确认它具有 discriminating power
        ↓
让 AI 自由寻找 implementation
        ↓
快速局部验证
        ↓
用独立、更高层的证据防止过拟合
        ↓
在 specification 边界内重构
```

这里最后那组高层证据很关键。

如果 AI 看到了所有 unit tests，我们还可以用：

```text
Unit/property
        +
Integration
        +
E2E acceptance
```

形成独立证据。

于是 AI 即使“作弊”满足了某一层，也很难同时欺骗所有具有不同 observation boundary 的证据。

这再次回到了我们之前说的：

> **互补证据产生杠杆。**

---

所以我现在会对 TDD 做一个比较严格的限定：

它最值得使用在满足这些条件的地方：

- 行为语义已经比较清楚；
- oracle 便宜、稳定、可信；
- 能用 property/contract 描述而不是强绑定实现；
- feedback 足够快，可以形成紧密循环；
- 实现空间仍然值得探索。

而下面这些情况就应该谨慎：

- requirement 本身仍处于探索阶段；
- 测试只能通过大量 mock 表达；
- oracle 很模糊；
- 高层系统 interaction 才是真正语义；
- test-first 会强迫你提前决定架构；
- 为了“Red”而制造没有信息价值的测试。

所以我不会把我们最后采用的方法称为：

> “所有代码必须 TDD。”

更合理的是：

> **Specification-first where specification is mature; exploration-first where product understanding is immature.**

然后利用自动化验证让两者最终汇合。

我认为到这里，TDD 的核心理论已经足够了。下一步如果沿主线走，一个非常自然的问题是 **TDD 与设计到底是什么关系**：所谓“tests drive design”究竟为什么会发生？哪些设计属性会被好的测试自然推出来，又为什么 mock-heavy TDD 会推导出另一种截然不同的 architecture。这个问题会直接把 TDD 接回我们之前的 testability 和系统设计。