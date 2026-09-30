# T04 | turn 21b2f931-9c2a-470b-af96-7891f64e4a66 | startedAt 1787721585.747999


## userMessage | message 21b2f931-9c2a-470b-af96-7891f64e4a66


同意。那我们开始吧。

## agentMessage | message 6844d8a8-2ef2-4d02-91be-23e08fc635bb


那就从第一课开始，只解决一个问题：

> 一个自动化测试，究竟凭什么能够说“软件是对的”？

答案是：它需要一个 **Test Oracle（测试判定准则）**。

你可以先把任何自动化验证都抽象成：

```text
输入 / 场景
   ↓
运行系统
   ↓
观察结果
   ↓
Oracle 判断
   ↓
Pass / Fail / Score
```

例如：

```python
result = add(2, 3)
assert result == 5
```

真正有价值的并不是 `assert` 这个语法，而是：

```text
result 应该等于 5
```

这句话。

因为它定义了“正确”。

---

这里要先区分三个东西。

假设产品需求是：

> 用户登录之后应该看到自己的 Dashboard。

这是 **requirement**。

我们把它具体化：

```text
Given:
  一个已注册用户

When:
  输入正确账号密码并登录

Then:
  页面进入 /dashboard
  显示用户自己的名字
```

这是更接近 **specification**。

自动化测试真正运行时可能是：

```python
page.fill("#email", user.email)
page.fill("#password", password)
page.click("Sign in")

expect(page).to_have_url("/dashboard")
expect(page.locator("h1")).to_contain_text(user.name)
```

这里的：

```text
URL == /dashboard
页面包含 user.name
```

就是 oracle。

所以可以形成第一个关系：

```text
Requirement
    ↓ concretize
Specification
    ↓ executable form
Oracle
```

这是后面所有测试理论的基础。

---

为什么这个概念特别重要？

因为大量“测试写得很多但软件还是不可靠”的项目，问题并不在测试执行器，而在 oracle 太弱。

例如需求：

> 用户付款后订单应该成功。

测试写成：

```python
response = POST("/checkout")
assert response.status_code == 200
```

这个测试可能完全通过，但：

```text
订单没有保存
钱扣了两次
库存没减少
confirmation email 没发
页面显示失败
```

都可能发生。

因此：

```text
status == 200
```

只是一个很弱的 oracle。

如果真正关心产品结果，oracle 应该靠近：

```text
order exists
payment captured exactly once
inventory reserved
user sees confirmation
```

这就是我们课程里很重要的一条原则：

> 测试质量首先取决于 oracle 的质量，而不是测试代码量。

---

第二个重要问题是：

> Oracle 从哪里来？

通常有几种来源。

最简单的是明确的业务规则：

```text
折扣后价格不得小于 0
用户名必须唯一
账户余额不得被重复扣款
```

这类 oracle 很强，因为预期结果明确。

第二种来自不变量：

```text
转账前后的资金总额不变
排序之后元素数量不变
serialize → deserialize 后数据不变
```

这里甚至不需要知道完整正确答案，只需要知道：

```text
某种性质永远成立
```

这以后会自然进入 property-based testing。

第三种来自参考实现：

```text
new_algorithm(input) == old_algorithm(input)
```

这叫 differential testing 的基本思想。

第四种来自外部状态：

```text
数据库最终是什么状态
文件是否真的创建
消息是否真的发出
浏览器里用户到底看到了什么
```

E2E 测试大量使用这种 oracle。

第五种不是简单的 correctness，而是 threshold：

```text
p95 latency < 200ms
memory < 500MB
error rate < 0.1%
```

这时候 oracle 已经开始从：

```text
expected == actual
```

变成：

```text
measurement satisfies constraint
```

这也是 testing 向 evaluation 过渡的地方。

---

现在回到你的 AI 持续迭代场景。

假设你对 AI 说：

```text
把登录速度优化一下。
```

这是一个很差的 autonomous iteration specification。

AI 修改代码以后，没有明确方法知道自己是否完成任务。

但如果给它：

```text
Functional:
- 所有现有 login E2E tests 必须通过

Performance:
- login API p95 < 150ms
- login API p99 < 300ms

Correctness:
- incorrect password 仍然返回 401
- successful login 仍然建立正确 session

Regression:
- unit + integration suite 全部通过
```

那么 AI 得到的是：

```text
修改
 ↓
运行
 ↓
获得失败信息
 ↓
定位
 ↓
继续修改
```

这里真正让 AI 能够迭代的，并不是“测试”这个名词。

而是：

> **machine-readable oracle。**

没有 oracle：

```text
AI → code
```

有 oracle：

```text
AI → code → feedback → correction → code → ...
```

所以从 autonomous software development 的视角，我甚至会把测试定义成：

> **给软件开发过程提供可执行反馈的机制。**

而不是传统教材里比较窄的“发现 bug 的活动”。

---

不过这里马上出现一个很深的问题。

假设需求是：

> Dashboard 应该加载得很快。

oracle 写成：

```text
load_time < 2s
```

问题来了：

为什么是 2 秒？

在什么机器上？

网络条件是什么？

冷启动还是热启动？

测一次还是测 1000 次？

p50 还是 p99？

数据库里有多少数据？

这说明：

> 把 requirement 转化成 oracle，本身就是一个工程设计过程。

很多时候，真正困难的工作不是写：

```python
assert latency < 200
```

而是定义：

```text
latency
```

到底是什么意思。

这就是为什么产品需求：

```text
fast
reliable
easy to use
secure
scalable
```

不能直接自动化。

必须经过：

```text
Product intent
     ↓
observable property
     ↓
metric / state
     ↓
measurement procedure
     ↓
threshold
     ↓
oracle
```

例如：

```text
“搜索要快”
 ↓
用户发出请求到首屏结果出现
 ↓
end-to-end latency
 ↓
1000 个 representative queries
 ↓
p95
 ↓
p95 < 800ms
```

这才真正变成了 AI 可以工作的 specification。

---

所以这一课最重要的 mental model 只有三个：

```text
1.
没有 Oracle，就没有真正的自动验证。

2.
Oracle 应该描述 observable behavior/property，
而不是实现细节。

3.
把产品需求转成 Oracle，
本身就是软件工程的一项核心工作。
```

尤其第三条，我认为和你的目标关系最大。

以后 AI 写代码会越来越便宜，而真正困难的部分会逐渐移动到：

```text
What should the system do?

What should never happen?

What should we measure?

Under what conditions?

What counts as good enough?
```

这些其实都是 oracle design。

下一步自然要讨论一个问题：

> **什么东西值得成为 Oracle？**

也就是如何从产品需求里提取：
**example、property、invariant、postcondition、metric、threshold**。

这是从“我有一个需求”走到“AI 可以自动验证这个需求”的关键一步。