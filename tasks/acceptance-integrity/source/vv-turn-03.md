# T03 | turn eaebf052-7244-45ba-95c4-85b0d0916c3c | startedAt 1787721206.239118


## userMessage | message eaebf052-7244-45ba-95c4-85b0d0916c3c


这个路线不错。但我还补充一些我自己的思考：我是为了让AI能持续迭代软件，所以才来学习这些；因为AI/LLM只是文本生成器，静态检查成本很低、反馈很快；但自动化测试特别是端到端的、能测试软件是否满足产品需求、技术需求（延迟）的测试，才能真正服务“迭代”，因为软件本身没有意义，它只是产品落地的一种形态。

## agentMessage | message efb1e459-6253-4cab-aca3-b4671a0c1bfb


对，这个补充把学习目标定义得更准确了。

你真正想研究的不是“软件测试”本身，而是：

> 如何把产品意图和工程约束，转化成 AI 可以反复执行、获得反馈、继续修改的软件迭代闭环。

这和普通开发者学习测试的出发点有明显区别。

你可以把 AI 开发软件理解成一个控制系统：

```text
产品需求 / 技术需求
        ↓
      Specification
        ↓
AI 修改软件
        ↓
运行 / 构建 / 部署
        ↓
自动化验证与测量
        ↓
structured feedback
        ↓
AI 判断问题并继续修改
        └──────────────↺
```

这里最重要的一点正是你说的：**代码本身不是最终目标。**

代码只是产品行为的一种实现。所以：

```text
代码正确
≠
软件正确
≠
产品正确
```

例如一个搜索产品，AI 可以做到：

```text
typecheck ✓
lint ✓
unit tests ✓
API integration ✓
```

但实际产品可能仍然：

```text
搜索结果质量差
响应 4 秒
手机端无法完成核心流程
错误提示让用户不知道该怎么办
高并发时 p99 延迟爆炸
```

所以如果目标是让 AI 持续迭代产品，只做 code-level testing 显然不够。

我更愿意把你要建立的体系称为：

**Executable Product Specification（可执行的产品规格）**

也就是尽可能把：

```text
产品需求
技术需求
设计约束
业务规则
性能目标
可靠性目标
```

变成机器能够执行和判断的东西。

例如产品需求：

> 用户注册后应该能够在一分钟内完成第一个项目创建。

可以逐步机器化为：

```text
Scenario:
  fresh user
  → signup
  → onboarding
  → create project

Assertions:
  project exists
  correct owner
  dashboard displays project
  no unhandled errors

Measurements:
  end-to-end latency < X
  API p95 < Y
  error rate < Z
```

这已经远远超过传统意义上的“给函数写 unit test”。

---

因此，对 AI iteration 来说，我认为测试应该按“反馈距离”来理解，而不只是传统的 test pyramid。

最里面：

```text
Static feedback
```

lint、type checking、compiler、schema、格式检查。

特点：

```text
极便宜
极快
定位精确
但是能证明的事情很少
```

下一层：

```text
Unit / component feedback
```

判断局部逻辑、边界条件、不变量。

特点：

```text
便宜
快
定位很好
但是距离产品行为仍然较远
```

再往外：

```text
Integration feedback
```

数据库、API、消息队列、filesystem、第三方接口。

开始验证：

> “这些真实组件组合以后还能不能工作？”

然后是你特别关注的：

```text
End-to-End / Acceptance feedback
```

直接从产品场景出发：

```text
用户能不能注册？
能不能完成购买？
能不能创建项目？
权限是否真的生效？
刷新页面之后数据还在不在？
```

这一层非常适合成为 AI agent 的“最终 oracle”。

因为它不关心：

> “你到底把代码怎么改的？”

只关心：

> “需求现在满足了吗？”

这其实给 AI 很大的实现自由度。

---

还有另外一个维度不能混进 test level：

**Non-functional requirements。**

比如：

```text
latency
throughput
memory
CPU
startup time
bundle size
reliability
availability
accessibility
security
```

这些通常不适合写成普通的：

```python
assert result == expected
```

而更像：

```text
p95 latency < 200 ms
p99 latency < 500 ms
memory < 500 MB
LCP < 2.5 s
error rate < 0.1%
```

这时候 automation 的作用是进行 **measurement + threshold judgement**。

所以这是我们后面讨论“evaluation”时真正值得深入的地方：

> Test 往往在判断 correctness；evaluation 更多是在测量 quality。

但两者最后都可以成为 AI 的反馈信号。

---

这样一来，AI iteration 的反馈系统其实有三个性质需要同时优化：

```text
1. Feedback speed
2. Feedback fidelity
3. Failure localization
```

这是非常重要的 trade-off。

例如：

```text
Typecheck
5 秒
很容易定位
但只能验证类型性质
```

而：

```text
真实浏览器 E2E
2 分钟
更接近产品真实行为
但失败原因可能很难定位
```

真实 production-like benchmark：

```text
30 分钟
非常接近真实性能
但成本很高
```

所以目标绝对不是：

> “所有事情都写 E2E。”

而是建立一个 **feedback portfolio**：

```text
                 Fidelity ↑

Production eval       ●

E2E / acceptance      ●

Integration       ●

Unit          ●

Static    ●
────────────────────────→ Cost / latency
```

AI 每改一次代码：

```text
static
↓
unit
↓
integration
↓
critical E2E
```

全部通过以后才值得跑：

```text
full E2E
performance
load
compatibility
```

所以便宜的测试不是不重要。

恰恰相反，因为 AI 能高速修改代码，**便宜、快速、确定性的反馈价值会进一步增加**。

只是它们不能成为最终 oracle。

---

而你那句话：

> “软件本身没有意义，它只是产品落地的一种形态。”

实际上可以导出我们后面整个课程最重要的一条原则：

> **测试边界最终应该来自 product contract，而不是 code structure。**

因此我们之后不会以：

```text
如何测试 function
如何 mock class
如何用 pytest
```

作为主线。

而应该以：

```text
产品想保证什么？
↓
哪些性质可以机器验证？
↓
在哪一层验证成本最低？
↓
如何设计 test oracle？
↓
如何让反馈足够稳定、准确、可定位？
↓
如何把它放进 AI iteration loop？
```

为主线。

这也稍微修改了我们刚才的课程路线。我现在会把它定成：

```text
第一部分
Verification 的基础理论
什么叫“证明软件工作”

第二部分
Test oracle 与 specification
如何把需求转化成机器可判断的条件

第三部分
自动化测试层次
static → unit → integration → E2E → acceptance

第四部分
非功能质量的自动化 evaluation
latency / reliability / performance / security 等

第五部分
测试架构与 testability
如何让整个系统容易被自动验证

第六部分
TDD
测试如何反过来驱动实现和架构

第七部分
AI Continuous Iteration
如何组合以上反馈形成 autonomous development loop
```

这样的话，**TDD 反而不会是课程起点**。

因为对你的目标而言，更底层的问题是：

> 怎样把“我想让产品满足什么”变成一个机器能够可靠判断的 oracle？

这个问题我认为就是我们下一步应该真正深入的第一课。它也是 unit test、E2E、performance benchmark、acceptance test，乃至后来 AI eval 的共同理论基础。