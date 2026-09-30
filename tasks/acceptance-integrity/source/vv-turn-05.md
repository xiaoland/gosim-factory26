# T05 | turn a3495b75-c102-4deb-aa7e-3f82cf0091be | startedAt 1787721951.390675


## userMessage | message a3495b75-c102-4deb-aa7e-3f82cf0091be


这里面我十分担心的就是，如果dashboard的url变了？如果没有h1元素？但其实这也还是一个dashboard页面呢？
而且定义product requirement / specification 是很困难的事情，不过主要的阻碍点是“组织”、“表达”本身，我认为。

## agentMessage | message 558c3b49-dc2b-4ae0-adf9-e27a308d8b99


对，你碰到的是更核心的问题：**Oracle 很容易把“产品语义”错误地绑定到“实现表象”上。**

`URL == /dashboard`、存在 `<h1>`，都可能只是当前实现细节。真正的 requirement 可能只是：

> 登录成功后，用户能够进入自己的工作区，并看到属于自己的核心信息和可执行操作。

这和 URL、DOM 标签、甚至页面是不是传统“页面”都没有必然关系。

所以我会把刚才的模型再拆一层：

```text
Product requirement
        ↓
Semantic contract
        ↓
Observable evidence
        ↓
Test implementation
```

最重要的是不要把第二层和第三、四层混为一谈。

比如：

```text
Semantic contract:
用户登录后能够访问自己的 dashboard。
```

可能用这些 evidence 来判断：

```text
- 当前用户身份已经建立
- 用户自己的项目可以被看到
- 用户可以执行“创建项目”
- 其他用户的私有项目不可见
```

而具体测试今天可能用：

```text
URL
DOM selector
API response
database state
accessibility tree
```

明天完全可以换。

所以：

```text
expect(page).to_have_url("/dashboard")
```

不是 specification。

它只是**当前用于观察 specification 是否成立的一种探针**。

这一区分很重要，因为一个好的自动化验证体系应该允许：

> 产品契约保持稳定，而 observation mechanism 随实现变化。

比如测试代码可以尽量写成：

```python
login_as(alice)

assert user_workspace_is_available(alice)
assert user_can_see_project(alice, project_a)
assert user_cannot_see_project(alice, bob_private_project)
```

至于 `user_workspace_is_available()` 内部究竟检查 URL、accessibility tree、页面内容还是 API，可以随着产品实现演进。

这也是为什么 E2E 设计里，比 CSS selector 更值得重视的是**稳定的语义接口**，例如 accessibility role、稳定的 `data-testid`、领域级 helper，甚至专门的测试接口。

---

你第二点我也很认同，而且我认为比“怎么写测试”更深。

Product requirement 难，不一定主要难在“我们不知道产品应该做什么”。

很多时候脑子里其实知道：

> “登录之后应该进入自己的工作空间。”
>
> “搜索应该快。”
>
> “这个操作不能丢数据。”
>
> “普通用户不能看到管理员内容。”

真正困难的是把这些零散认识：

```text
想法
经验
例子
边界条件
业务规则
设计意图
性能目标
```

组织成一个**结构稳定、可以逐步细化、可以被机器消费的表示**。

这其实已经接近 **requirements engineering / specification engineering**，而不只是 testing。

我觉得可以把问题看成两步。

第一步是“组织”。

不要一开始试图写一份完美 PRD，而是把产品知识分成几种不同性质的东西：

```text
Capability
用户能够做什么

Rule
什么必须 / 不能发生

Invariant
无论如何始终成立什么

Scenario
在某种情境下应该发生什么

Quality attribute
要多快、多可靠、多安全

Example
一个具体的正确案例
```

例如 Dashboard：

```text
Capability
用户可以访问自己的工作空间

Rules
未登录用户不能访问
用户不能看到其他人的私有内容

Invariant
workspace 中显示的数据属于当前 identity 的权限范围

Scenario
登录成功 → 打开 workspace → 查看项目 → 创建项目

Quality
核心内容 p95 在 1s 内可交互
```

一下就比一大段自然语言清晰很多。

然后第二步才是“表达”。

其中一些最后变成：

```text
assertions
```

一些变成：

```text
E2E scenarios
```

一些变成：

```text
performance benchmarks
```

一些甚至暂时只能保留为：

```text
human-reviewed requirement
```

**不是所有 requirement 都必须立刻 executable。**

---

而且这里对 AI development 有一个特别重要的结论。

未来真正有价值的 artifact 可能不只是代码库，而是：

```text
Product model
      +
Executable specification
      +
Implementation
```

AI 可以不断重写第三个。

第二个负责告诉它：

> 你改坏了吗？

第一个负责告诉它：

> 我们到底为什么要这样做？

所以你说“主要阻碍是组织和表达”，我认为很准确。

我们接下来甚至可以暂时不谈测试框架，而专门研究一个问题：

> **怎样组织 Product Specification，使它既足够接近人的产品意图，又能逐渐转化成稳定的 automated oracle？**

我觉得这会比继续讲 unit/integration/E2E 更接近你真正要解决的问题。