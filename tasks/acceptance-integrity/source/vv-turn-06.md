# T06 | turn bf1f0fbb-bcf4-44a8-8429-e54a53956e81 | startedAt 1787723829.153284


## userMessage | message bf1f0fbb-bcf4-44a8-8429-e54a53956e81


分层是正确的，但是怎么保证这些层之间没有发生偏移呢？
你说把产品知识分成几种不同的东西，但没有论证为什么分类可以解决这个问题，也没有给出这样分类的依据。

## agentMessage | message b0f97c5c-1737-46cf-9ed1-484859126e3e


对。这里需要把问题说得更严格一些。我上一条给出的分类其实不够好，因为它混合了两个不同维度：

- `capability / invariant / quality` 是“要求的语义类型”；
- `scenario / example` 是“表达或验证这种要求的方法”。

所以那套分类本身确实没有理论依据，也不能解决层间漂移。

更准确的问题应该是：

> 如果上层表达的是产品语义，下层是 executable specification，什么条件下我们可以认为下层仍然忠实于上层？

这其实是一个 refinement（逐层精化）问题。

可以把整个体系写成：

```text
Product intent
      ↓ refinement
Semantic specification
      ↓ operationalization
Observable specification
      ↓ implementation
Automated oracle
```

关键不在有几层，而在每一条箭头都必须承担一个“证明义务”。

比如：

```text
R:
登录用户能够使用自己的 workspace
```

下面有一个测试：

```text
O:
assert URL == "/dashboard"
assert <h1> exists
```

我们应该问：

> 为什么 O 成立能够证明 R 成立？

实际上证明不了。

反过来也有问题：

> 如果 R 成立，O 是否应该成立？

也不成立——URL 可以变，`h1` 可以消失。

所以这个 oracle 与 requirement 之间没有可靠的 refinement relation。

---

一个很有用的判断标准是 **representation invariance**。

假设从产品角度，下面两个实现完全等价：

```text
Implementation A
/dashboard
<h1>My Workspace</h1>

Implementation B
/home
<div role="heading">My Workspace</div>
```

如果产品需求根本不关心 URL 和 HTML tag，那么：

```text
A ≈product B
```

一个产品级 oracle 应该满足：

\[
A \approx_{product} B
\Rightarrow
Oracle(A)=Oracle(B)
\]

也就是说：

> 对产品语义无关的实现变化，oracle 应该保持不变。

这就是你刚才提出 Dashboard 例子的理论核心。

相反，如果：

```text
A:
Alice 只能看到 Alice 的项目

B:
Alice 可以看到 Bob 的 private project
```

那么：

```text
A ≉product B
```

oracle 就必须能够区分它们。

所以一个好的 oracle 要同时满足两个方向：

```text
semantic change
→ 应该敏感

implementation-only change
→ 应该不敏感
```

这比“不要依赖 CSS selector”更本质。

---

而你问的第二个问题——分类依据是什么——我会重新建立在“系统行为的数学对象”上。

假设软件执行可以抽象成：

```text
state
action
state
action
state
...
```

也就是一条 execution trace。

产品要求实际上主要是在约束几种不同对象。

第一种是 **状态性质**：

```text
P(state)
```

例如：

```text
订单金额 >= 0
当前用户看不到无权限数据
```

其中“所有 reachable state 都成立”的就是 invariant：

\[
\forall s \in Reachable,\quad P(s)
\]

第二种是 **操作/状态转移性质**：

```text
P(before, action, after)
```

例如：

```text
Given balance = 100
When withdraw(30)
Then balance = 70
```

这就是 precondition / postcondition / contract 一类东西。

第三种是 **时间/流程性质**：

它约束的是整个 trace。

例如：

```text
用户成功付款
→ 最终一定能看到订单确认
```

或者：

```text
登录
→ 创建项目
→ 项目最终出现在项目列表
```

这属于 temporal / behavioral property。

第四种是 **量化性质**：

它不是简单 true/false，而是：

\[
metric(behavior, workload)
\]

例如：

```text
p95 latency
error rate
throughput
memory
```

然后才有：

\[
p95(latency) < 200ms
\]

这种 quality constraint。

这几种分类有一个比较坚实的依据：

> 它们分别是在约束 state、transition、trace 和 distribution/measurement。

而：

```text
example
scenario
counterexample
test case
```

不是同一层面的 requirement 类型。

它们是我们用来**实例化或验证这些性质的证据**。

这是我上一条里需要纠正的地方。

---

现在回到“怎么避免层间偏移”。

实际上无法做到绝对保证——只要最上层还是人的自然语言意图，就永远存在解释空间。

但我们可以建立三个非常强的机制。

第一是每次 refinement 都明确写：

```text
Requirement:
用户可以访问自己的 workspace

Product-relevant observables:
- 当前身份是 Alice
- Alice 的项目可见
- Bob 的私有项目不可见
- Alice 可以创建项目

Irrelevant implementation details:
- URL
- DOM structure
- CSS
- React component hierarchy
```

这里其实是在定义：

> 什么变化算产品变化，什么变化不算。

这一步非常关键。

第二是对每个 oracle 问两个对称的问题：

```text
1. 如果产品需求被破坏，
   这个测试一定会失败吗？

2. 如果只是实现方式改变，
   但产品需求仍然成立，
   这个测试会不会错误失败？
```

第一个问题检查 **oracle 太弱**。

第二个检查 **oracle 太具体**。

Dashboard URL 测试的问题主要就是第二种。

第三个机制甚至可以自动化：**故意制造 semantic mutation 来测试测试本身。**

例如 requirement：

```text
Alice 不能看到 Bob 的 private project
```

故意修改系统：

```text
permission_check() 永远返回 true
```

然后看 acceptance test 是否失败。

如果没失败，就说明：

> 测试虽然是绿色的，但根本没有覆盖那个 product contract。

这其实比 code coverage 更接近我们真正关心的问题。

---

因此我觉得我们已经得到一个比“测试金字塔”更重要的模型：

```text
Product semantics
        ↓
定义什么变化是有意义的
        ↓
Behavioral properties
        ↓
定义可观察证据
        ↓
Oracle
```

而检验这个链条的方法不是问：

> “有没有测试？”

而是问：

> **这个 oracle 对 semantic changes 敏感，同时对 semantic-preserving implementation changes 不敏感吗？**

这可能是我们整个讨论里第一个真正足够扎实的原则。

下一步值得继续沿着这里走：**Product intent 如何被组织成 behavioral properties，而又不过早绑定实现。**这会进入 specification 的核心，而不是测试工具本身。