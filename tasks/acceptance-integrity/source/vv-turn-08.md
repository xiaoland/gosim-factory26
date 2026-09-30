# T08 | turn 3fce243e-799d-44bc-8dc0-b211e68d2a41 | startedAt 1787793140.033879


## userMessage | message 3fce243e-799d-44bc-8dc0-b211e68d2a41


好的，那我们继续

## agentMessage | message 98bc0282-9e1b-459d-8abc-799893c9ccf9


继续。这一课的核心问题是：

> 软件行为空间近乎无限，为什么有限测试仍然有意义？

最重要的答案其实有点“不舒服”：

**有限测试通常不能证明程序对所有情况都正确。它只能在某些假设之下，提供不同强度的证据。**

这和上一课的结论很像：我们无法消除不确定性，只能系统地控制它。

假设有：

```python
def discount(price, user_type, coupon, region, time):
    ...
```

即使每个参数只有几十种可能，组合空间也会迅速爆炸。真实软件再加入数据库状态、调用顺序、并发、网络错误、历史操作以后，基本不可能 exhaustive testing。

因此 testing 的真正问题不是：

> “怎样测试所有情况？”

而是：

> “依据什么理由，把巨大的行为空间压缩成少量有代表性的测试？”

这就是 **test selection / test design**。

一个很重要的 mental model 是：

```text
Behavior space
      ↓
我们对系统结构和故障模式的假设
      ↓
划分 / 抽样 / 构造特殊情况
      ↓
有限 test set
```

关键在中间那层“假设”。

比如函数：

```python
def shipping_fee(weight):
    if weight <= 1:
        return 5
    elif weight <= 10:
        return 10
    else:
        return 20
```

输入重量理论上有无限多个：

```text
0.001
0.002
0.003
...
```

但你很自然会觉得：

```text
0.5
0.7
0.9
```

没必要全部测。

为什么？

因为你隐含做了一个假设：

> `0 < weight <= 1` 这一段里的输入，对程序来说属于同一种行为类别。

这就是 **equivalence partitioning（等价类划分）**。

于是：

```text
(-∞, 0]      invalid?
(0, 1]       fee = 5
(1, 10]      fee = 10
(10, ∞)      fee = 20
```

每个区域选一个代表值。

这并不是数学证明。

它实际上是在说：

> “我相信同一个 partition 内部出现不同 bug 的概率比较低。”

因此测试设计本质上一直依赖 **fault model**：

> 我认为 bug 通常会以什么形式出现？

---

而经验告诉我们，bug 特别喜欢发生在 partition 的交界处。

所以有了第二种方法：

**Boundary Value Analysis。**

上面的程序，比起测：

```text
5
6
7
```

更值得测试：

```text
0
0.0001

1
1.0001

10
10.0001
```

因为典型 bug 是：

```python
if weight < 1:
```

和：

```python
if weight <= 1:
```

写错。

所以：

```text
equivalence partitioning
```

是在压缩空间；

```text
boundary analysis
```

是在把测试预算集中到高风险位置。

---

但并不是所有软件都可以只看输入值。

例如登录系统：

```text
logged_out
  ↓ login
logged_in
  ↓ logout
logged_out
```

这里：

```text
logout
```

在不同 state 下语义不同。

于是我们需要测试：

```text
state × action → next state
```

这就是 **state-transition testing**。

例如：

```text
logged_out + access dashboard
logged_out + login success
logged_out + login failure

logged_in + access dashboard
logged_in + logout
session_expired + access dashboard
```

这里测试空间不是普通的 input space，而是：

> execution histories。

这对你关心的 E2E 尤其重要，因为产品需求大量是 workflow，而不是函数输入输出。

---

再复杂一点，会出现组合爆炸。

例如：

```text
browser:
Chrome / Safari / Firefox

OS:
Windows / macOS / Linux

account:
free / pro / enterprise

auth:
password / Google / SSO
```

全组合：

\[
3\times3\times3\times3=81
\]

现实系统可能是几十个维度。

这时一个重要经验是：

> 很多 interaction bug 是少数几个变量共同作用造成的。

因此可以使用 **combinatorial testing / pairwise testing**：

不测试全部组合，而确保：

```text
任意两个参数值的组合
至少出现一次
```

例如不一定测试 81 个 case，也许十几个 case 就覆盖全部 pair。

这里仍然没有证明。

背后的 fault model 是：

> 大部分 interaction failures 是低阶 interaction 导致的。

如果你的系统恰好存在一个：

```text
Safari
+ macOS
+ enterprise
+ SSO
```

四个条件同时触发的 bug，pairwise 可能完全发现不了。

所以所有 test selection technique 都有自己的 blind spot。

---

这带出了一个我认为非常重要的概念：

## Coverage 不是“测试了多少代码”，而是“你选择覆盖哪个空间”

我们经常一提 coverage 就想到：

```text
line coverage = 87%
```

但 coverage 的概念其实远远更一般：

```text
Requirements coverage

Input partition coverage

Boundary coverage

Branch coverage

Condition coverage

State coverage

Transition coverage

API endpoint coverage

User journey coverage

Browser/device coverage

Fault scenario coverage
```

Coverage 真正表达的是：

\[
\frac{\text{我们实际覆盖的元素}}
{\text{我们认为值得覆盖的元素}}
\]

所以在问：

> “coverage 是多少？”

之前，更重要的问题其实是：

> **coverage of what?**

例如：

```text
100% line coverage
```

完全可能没有测：

```text
并发
错误恢复
极端数据量
两个 feature 的交互
真实浏览器行为
```

因此 100% line coverage 从来不等于“产品得到了充分测试”。

---

还有一种不同的路线非常重要：

**Property-based testing。**

传统 example：

```python
assert sort([3, 1, 2]) == [1, 2, 3]
```

Property：

```text
对于任意 list：

sort(xs) 的长度 == xs 的长度

sort(xs) 中的元素集合 == xs

sort(xs) 是非递减的
```

于是：

```python
@given(lists(integers()))
def test_sort(xs):
    result = sort(xs)

    assert len(result) == len(xs)
    assert Counter(result) == Counter(xs)
    assert result == sorted(result)
```

这里你做了一件非常重要的事情：

```text
人工选择 inputs
```

变成：

```text
人工定义 properties
+
机器生成 inputs
```

这对于 AI 自动迭代特别有价值。

因为 AI 很容易：

```text
修到现有 17 个 example 都通过
```

但 property-based testing 可以不断产生你没有明确写出来的 case。

这相当于降低对固定 regression suite 的过拟合。

---

再进一步就是 fuzzing。

它的思路更激进：

> 我甚至不一定知道“正确输出是什么”，但我可以大量生成奇怪输入，看系统会不会出现某些绝对不能出现的结果。

例如 parser：

```text
随机 byte sequence
↓
parser
```

Oracle 可能只有：

```text
不能 crash
不能 hang
不能 memory corruption
```

这也是 test selection。

只不过策略变成：

> 大规模探索 input space。

---

把这些放在一起，你会发现测试设计实际上有几类不同的“空间压缩方法”：

```text
Equivalence partitioning
→ 把相似行为归类

Boundary analysis
→ 集中攻击边界

State testing
→ 覆盖重要状态和转移

Combinatorial testing
→ 覆盖变量交互

Property-based testing
→ 定义一般性质，让机器探索输入

Fuzzing
→ 大规模探索异常输入

Regression cases
→ 保留历史上已经发生的失败

Risk-based testing
→ 把资源投到后果最严重的位置
```

它们没有谁能够取代其他方法。

因为它们分别针对不同的 fault model。

---

这时候可以回答这一课最初的问题了。

有限测试为什么有意义？

不是因为：

```text
100 tests
≈
证明全部行为正确
```

而是因为我们系统性地构造：

```text
representative cases
+
dangerous boundaries
+
important state transitions
+
likely interactions
+
general properties
+
known historical failures
+
high-risk scenarios
```

于是有限测试集成为：

> 对我们当前 fault model 的系统性挑战。

我很喜欢把一个 test suite 理解成：

**一套关于“这个软件可能怎样坏掉”的编码知识。**

这也解释了为什么成熟软件的测试集会越来越有价值。

每出现一次 bug：

```text
“原来系统还能这样坏。”
```

就可以加入一个新的 failure model：

```text
bug
↓
understanding
↓
regression test
```

测试集因此不断积累工程知识。

---

对于你的 AI iteration 场景，这里还有一个特别重要的推论。

AI 面对：

```text
固定的测试集
```

很容易优化成：

```text
make tests green
```

而不是：

```text
make product correct
```

这实际上和机器学习里的 overfitting 很像。

所以一个适合 AI 持续迭代的 verification system，最好不要只有：

```text
fixed regression examples
```

还应该有：

```text
fixed regression suite
+
generated cases
+
properties
+
randomized inputs
+
hidden / held-out scenarios
+
periodically refreshed E2E scenarios
```

这样 AI 面对的不是一张固定答案表，而是一个持续产生 challenge 的环境。

---

所以这一课我希望你只留下三个概念：

> **第一，测试永远是在抽样，除非问题足够小到能 exhaustive verification。**

> **第二，test selection 的依据不是随便挑 case，而是 fault model：你认为软件可能怎样失败。**

> **第三，coverage 只是 test adequacy 的一种代理指标；任何 coverage 都必须先问 “coverage of what?”。**

到这里，我们已经有了自动化验证的两个基础轴：

```text
             Automated verification

        Test selection     Test oracle
         测什么？          怎么判断？
             │                │
             └────────┬───────┘
                      ↓
                 Test evidence
```

主线下一步我建议进入一个非常关键的问题：

> **Test suite 到底应该怎样分层？为什么会有 unit / integration / E2E，它们真正的区别究竟是什么？**

这时我们再谈 test pyramid，就不会变成“unit 多写一点、E2E 少写一点”这种经验口诀，而能从反馈成本、真实性、故障定位和产品语义的角度推导出来。