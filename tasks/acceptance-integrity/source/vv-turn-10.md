# T10 | turn fe176c23-d1eb-409f-aed0-ebaddfc21d4b | startedAt 1787914732.983915


## userMessage | message fe176c23-d1eb-409f-aed0-ebaddfc21d4b


这个观察和分析很到位，解答了我一直以来讨厌regression tests但是问题真实存在而我没有解决方案的问题，你的解决方案是符合因果的、洞察到本质的。  
同意接下来进入测试分层，毕竟测试也是有成本的。

## agentMessage | message 6ed42cc6-aef2-4a2c-8a55-315c1351e4cb


好，那测试分层可以从一个非常简单的问题推出来：

> 对某个“正确性约束”，我们应该在多大的系统边界上验证它？

我认为这比从 `unit / integration / E2E` 的定义背起更有用。

核心原则可以先记成一句话：

> **在仍然保留目标语义的前提下，选择成本最低、反馈最快、定位最清晰的测试边界。**

这句话基本可以推导出整个测试分层。

假设有一个产品规则：

```text
用户不能读取其他用户的私有项目。
```

你可以在很多层验证。

最小边界可能是：

```python
assert policy.can_read(alice, bob_private_project) is False
```

这是 unit-level。

扩大一点：

```text
GET /projects/bob-private
Authorization: Alice

→ 403
```

这是 integration/API-level。

再扩大：

```text
Alice 登录浏览器
→ 尝试打开 Bob 的私有项目
→ 看不到内容
```

这是 E2E。

这三个测试表面上都在验证同一件事，但提供的证据不同。

Unit test 证明：

> 权限判定逻辑本身满足这个 property。

API test 进一步证明：

> HTTP routing、authentication、authorization、repository 等组合后，仍然保持这个 property。

E2E 又进一步证明：

> 从真实用户入口进入以后，整个产品确实没有泄漏这个信息。

所以测试层级真正改变的是：

> **我们允许多少真实系统参与这个实验。**

---

这就产生了一个非常重要的 trade-off。

系统边界越小：

```text
速度快
↓
稳定
↓
失败容易定位
↓
环境便宜
```

但同时：

```text
能够证明的系统级事实越来越少
```

系统边界越大：

```text
更接近真实产品
↓
覆盖真实组件交互
↓
能验证更高层语义
```

但：

```text
慢
昂贵
更容易 flaky
失败原因更难定位
```

所以不是：

> Unit 好，E2E 坏。

而是：

> **证据强度和反馈成本之间的交换。**

可以画成：

```text
                   Product fidelity
                         ↑

E2E                     ●
                      /
Integration          ●
                  /
Component        ●
              /
Unit         ●
────────────────────────────→
       Cost / latency / ambiguity
```

这里最后那个 ambiguity 很重要。

一个 unit test 失败：

```text
calculate_discount()
expected 80
actual 90
```

原因范围很窄。

但一个 E2E：

```text
Checkout failed
```

原因可能是：

```text
frontend
API
authentication
database
payment sandbox
queue
network
test environment
browser
test本身
```

所以 E2E 的“产品真实性”高，但 diagnostic resolution 低。

---

由此可以重新定义几个常见层级。

### Unit

不是简单：

> “测试一个 function。”

更准确是：

> **在一个很小的 behavioral boundary 内验证 property，并把大部分外部环境排除掉。**

例如：

```text
discount calculation
permission decision
parser
state transition
domain invariant
```

尤其适合你刚才喜欢的：

```text
property
invariant
contract
```

因为这些东西往往可以脱离整个产品运行。

这就是 unit test 最大的价值：

> 用极低成本，对 specification 的大量区域形成非常密集的约束。

---

### Integration

Integration 的问题是：

> **几个 individually-correct 的组件组合起来后，contract 是否仍然成立？**

因为很多错误并不发生在组件内部，而发生在边界：

```text
A 认为 timestamp 是 UTC
B 认为 timestamp 是 local time
```

单测：

```text
A ✓
B ✓
```

组合：

```text
A + B ✗
```

典型 integration boundary 有：

```text
application ↔ database
service ↔ service
backend ↔ queue
API ↔ authentication
application ↔ filesystem
```

这层本质上是在验证：

> **composition correctness。**

这也是为什么“大量 mock 的 unit test”可能让人产生虚假的安全感。

如果：

```text
mock database
mock auth
mock payment
mock queue
```

全部按照你想象中的 contract 工作，那么 test 只证明：

> 如果世界和我想象的一样，我的代码能工作。

Integration test 则开始验证：

> 世界是不是实际上和我想象的一样。

---

### End-to-End

E2E 的真正价值不是：

> “把所有东西再测一次。”

它应该承担的是一种其他层无法提供的证据：

> **真实产品入口到真实产品结果之间的 contract 是否成立。**

比如：

```text
用户注册
→ 创建 workspace
→ 邀请 teammate
→ teammate 接受
→ 两人可以协作
```

这里真正关心的是：

```text
产品 capability 成立
```

而不是：

```text
某个 controller 返回了正确 JSON
```

所以 E2E 最适合表达：

```text
critical user journey
cross-system workflow
product acceptance criteria
```

而不应该用来测试所有边界情况。

比如：

```text
年龄 17
年龄 18
年龄 19
```

如果这只是一个纯业务规则，写三个浏览器 E2E 通常很浪费。

应该在 domain 层大量验证：

```text
age < 18 → forbidden
```

然后只保留少量 E2E，证明：

> 这个规则真的接入了产品流程。

---

这会得到一个非常实用的原则：

> **Lowest sufficient layer。**

对于每一个 property，都问：

> “在哪个最低层级，我还能真正观察到这个 property？”

例如：

```text
所有成功转账保持总资金量不变
```

domain-level 就足够：

```text
Unit / property test
```

没必要浏览器点 1000 次。

但：

```text
用户能够完成 OAuth 登录
```

如果 OAuth provider、redirect、cookie、browser behavior 本身就是需求的一部分，那么低层 mock 掉它们以后已经失去语义。

这种 property 就需要更高层测试。

---

这里也正好回应你最开始担心的：

```text
URL 改了怎么办？
h1 没了怎么办？
```

如果 E2E 本来验证的是：

> 用户进入 workspace。

那么 E2E 应该观察尽量贴近这个语义的东西。

例如：

```text
用户可以看到自己的项目
用户可以执行 workspace 的核心 action
```

而不是：

```text
URL 必须是什么
某个 DOM node 必须是什么
```

除非 URL 本身就是产品 contract。

所以 E2E 的脆弱性很多时候不是 E2E 天生导致的，而是：

> **测试 observation boundary 选对了，但 oracle 又下沉到了 implementation detail。**

---

测试分层还有另一个容易忽略的维度：

> **Environment realism。**

例如数据库测试可以有：

```text
pure unit
↓
SQLite in-memory
↓
local Postgres
↓
containerized production-version Postgres
↓
staging database
↓
production
```

它并不是一个简单的 unit/integration 二分。

随着 realism 增加：

```text
fidelity ↑
cost ↑
latency ↑
operational complexity ↑
```

所以测试架构其实是在选择很多个 sampling points：

```text
behavior boundary
×
environment realism
×
workload realism
```

这比“test pyramid”更准确。

---

现在可以谈经典 Test Pyramid 了。

它大概表达：

```text
        / E2E \
       /       \
      /Integration\
     /             \
    /     Unit      \
```

它真正值得保留的不是形状，而是经济学：

> **便宜测试多跑，昂贵测试少跑。**

但我不认为应该机械遵守：

```text
70% unit
20% integration
10% E2E
```

这种比例没有普遍意义。

例如纯算法库：

```text
unit/property tests 极多
E2E 接近没有
```

一个 glue-heavy SaaS：

```text
integration tests 很重要
```

一个浏览器 extension：

```text
真实 browser E2E 可能比很多 mocked unit test 更有价值
```

所以测试结构应该由：

```text
系统风险
+
系统边界
+
产品 contract
+
反馈成本
```

共同决定。

---

这里还有一个很重要的原则，和我们上一轮关于 regression 的讨论一致：

**不要重复验证 implementation，而应该形成互补证据。**

比如：

```text
Unit:
permission invariant

Integration:
HTTP request 真正调用 permission layer

E2E:
用户最终无法看到 unauthorized resource
```

这是合理的，因为三层回答三个不同的问题。

但如果是：

```text
Unit:
assert button text == "Create"

Integration:
assert button text == "Create"

E2E:
assert button text == "Create"
```

除非按钮文本本身是产品要求，否则只是三倍维护成本。

因此分层不是：

> 同一个 test 写三遍。

而是：

> **每一层消除一种不同的不确定性。**

我觉得这句话值得记住。

---

现在把它放回 AI 持续迭代。

一个非常自然的执行顺序就是：

```text
AI 修改代码
    ↓
static checks
    ↓
small/local properties
    ↓
integration contracts
    ↓
critical product E2E
    ↓
performance / reliability evaluation
```

为什么这个顺序合理？

不是因为大家习惯这么写 CI。

而是因为它遵循：

```text
cheap + precise
        ↓
expensive + realistic
```

假设 unit 已经失败：

```text
余额 invariant 被破坏
```

就完全没理由继续花 10 分钟跑浏览器测试。

反过来，如果前面全部通过：

```text
unit ✓
integration ✓
```

E2E 失败就给 AI 一个很有价值的信息：

> 局部 properties 大概率成立，问题更可能存在于系统组合或产品路径。

测试分层因此不仅降低计算成本，也提高了 **diagnostic information**。

---

所以目前我们可以把测试分层压缩成三个原则：

**1. Lowest sufficient layer**

在不损失目标语义的前提下，在最低成本层验证。

**2. Each layer removes different uncertainty**

Unit 验证局部 property，integration 验证 composition，E2E 验证产品路径。

**3. More realism should buy more evidence**

如果一个更昂贵的测试没有增加新的可信证据，它通常就不值得存在。

第三条尤其适合用来审视 E2E：

> “这个 40 秒的浏览器测试，到底证明了什么是 20ms 的 domain test 无法证明的？”

如果答案说不出来，很可能测试边界选错了。

下一步我认为应该继续沿“成本”往下走：**测试成本究竟由什么组成？** 因为运行时间其实只是其中很小的一部分。真正昂贵的往往是维护成本、flakiness、环境成本、诊断成本和 specification coupling。理解这个之后，我们才能认真回答“一个 AI-driven 项目应该投资多少自动化测试”。