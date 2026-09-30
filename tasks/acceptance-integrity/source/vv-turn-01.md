# T01 | turn a98c26d8-f2e2-4fe2-9479-330878b70300 | startedAt 1787706755.132


## userMessage | message a98c26d8-f2e2-4fe2-9479-330878b70300


今天，Eval-Driven development 和 Test-Driven development 都更加重要，然而在以前我个人的软件开发过程中，因为都是 side-project，在软件测试与验证上面，一直没有比较深入的经验，今天我的摸索也比较零碎，一直没有比较系统的理论，今天希望系统地学习一下。

## agentMessage | message 614d29d5-c1bb-43c8-95ae-8a9f2b58b8ce


你现在最值得建立的，不是“测试框架使用经验”，而是一套完整的“验证思维”。

可以把目标概括成一句话：

> 开发不是“写代码 → 看起来能跑”，而是“定义成功 → 建立证据 → 实现 → 持续验证 → 从失败中更新验证体系”。

TDD 和今天越来越重要的 Eval-Driven Development，本质上都属于这个思想，只是面对的软件性质不同。

截至 2026 年，TDD 已经是一套相当成熟的方法论；而 Eval-Driven Development 仍在快速形成实践规范，尤其集中在 LLM、Agent 和 AI-assisted software 上。OpenAI 将 eval 的基本循环概括为 Specify → Measure → Improve；Anthropic 最近对 agent eval 的总结也强调先定义成功、建立任务集与 graders，再迭代系统。:chatgpt-content-reference{index="0"}

## 一、先建立最重要的整体框架

传统软件里，我们通常面对的是：

\[
input \rightarrow deterministic\ program \rightarrow output
\]

同样的输入，大部分情况下应该产生同样的输出。

所以我们很容易写：

```text
given X
expect Y
```

例如：

```python
assert add(2, 3) == 5
```

但现代 AI 软件更接近：

\[
task + context + model + tools + environment + randomness
\rightarrow behavior
\]

你真正关心的可能不是：

```text
output == 某一个字符串
```

而是：

```text
它有没有完成用户任务？
事实是否正确？
有没有漏掉关键内容？
有没有违反约束？
工具调用结果正确吗？
用了多少钱？
花了多久？
重复跑 20 次能成功多少次？
```

于是验证方法从传统 assertion 扩展成了 evaluation。

所以我建议先形成这个认识：

| 方法 | 核心问题 |
|---|---|
| Static checks | 这段程序是否合法？ |
| Unit test | 一个局部行为是否正确？ |
| Integration test | 两个组件组合之后是否正确？ |
| Contract test | 两个系统是否遵守约定？ |
| E2E test | 整个用户流程是否工作？ |
| Performance / security test | 非功能属性是否达标？ |
| Eval | 整个系统表现“有多好”？ |
| Production monitoring | 在真实世界里实际上发生了什么？ |

这里有一个非常重要的认知：

**Eval 不是 test pyramid 最上面新加的一层。**

Eval 更像一个正交维度。

一个 eval 的 grader 本身可以是：

```text
unit tests
integration tests
static analysis
regex
JSON schema
database state
browser state
human judgment
LLM-as-a-judge
多个指标的组合
```

Anthropic 当前的 agent-eval 方法正是把 deterministic grader、model grader 和 human grader 混合起来使用。:chatgpt-content-reference{index="1"}

---

# 二、Testing 到底在解决什么问题？

可以把软件质量分成两个经典问题：

**Verification**

> Did we build the system right?

也就是：

“我们有没有按照规格正确实现？”

例如：

```text
calculateTax(100) 应该返回 8
API 返回 schema 是否正确
数据库 transaction 是否 rollback
```

而另一个是：

**Validation**

> Did we build the right system?

也就是：

“这个东西实际上有没有解决问题？”

例如一个 AI 搜索助手：

```text
回答 JSON schema 正确
```

可能 verification 完全通过。

但：

```text
答案没解决用户的问题
```

validation 仍然失败。

传统 automated testing 非常擅长 verification。

Eval 则往往同时覆盖 verification 和 validation。

这也是为什么进入 AI 软件开发以后，eval 的重要性突然明显增加。

---

# 三、TDD 真正是什么

很多开发者第一次接触 TDD，会把它理解成：

> “先写 unit test，再写 implementation。”

这个定义太浅了。

TDD 实际上是一种：

> **通过可执行行为规格来驱动软件设计的反馈循环。**

经典流程就是：

```text
Red
↓
Green
↓
Refactor
↓
Red
...
```

Martin Fowler 对 TDD 的概括也是：先为下一小块功能写测试，再写代码使测试通过，然后在测试保持通过的情况下重构。Kent Beck 的原始方法还强调，在进入循环前通常先列一份 test list。:chatgpt-content-reference{index="2"}

例如你要写：

```python
def withdraw(account, amount):
    ...
```

不要先设计：

```text
AccountService
TransactionManager
BalanceRepository
WithdrawalStrategy
...
```

而是先提出一个行为：

```python
def test_withdraw_reduces_balance():
    account = Account(balance=100)

    account.withdraw(30)

    assert account.balance == 70
```

Red。

然后写最低限度代码。

Green。

接下来发现：

```python
def test_cannot_overdraw():
    ...
```

继续 Red。

慢慢地，你的软件设计被真实需求“拉出来”。

这就是 TDD 很重要的一点：

**Test 不只是检查代码；test 会对设计施加压力。**

如果一个东西非常难测试，通常意味着：

```text
dependency 太多
global state 太多
side effect 太多
职责混在一起
boundary 不清晰
```

于是测试困难反过来成为设计反馈。

---

# 四、TDD 最容易学错的地方

TDD 不是追求：

```text
100% code coverage
```

也不是：

```text
每个 function 一个 test
```

更不是：

```text
把每一个 dependency 都 mock 掉
```

真正应该测试的是：

> observable behavior。

例如：

```python
class OrderService:
    def place_order(...):
        self.inventory.reserve(...)
        self.payment.charge(...)
```

坏测试经常是：

```text
assert reserve called exactly once
assert charge called exactly once
```

这很容易把测试绑定在 implementation 上。

你以后把：

```text
reserve()
charge()
```

重构成：

```text
checkout()
```

虽然功能完全一样，测试却全炸了。

更稳健的问题通常应该是：

```text
订单成功了吗？
库存真的减少了吗？
付款失败时订单有没有 rollback？
重复请求是否产生两笔订单？
```

也就是：

> 测试 contract，而不是实现过程。

这是以后做 Eval 时也会反复遇到的原则。

Anthropic 的 agent eval 指南也明确提到：不要过度要求 agent 按某个固定步骤完成任务，因为正确系统可能找到你没有预料到的路径；更好的方法往往是验证最终 outcome。:chatgpt-content-reference{index="3"}

---

# 五、传统软件测试应该形成什么能力

如果你的 side-project 以前基本靠手动点一遍，我会把学习重点放在下面这个能力链。

```text
pure logic
    ↓
unit test

database / filesystem / external API
    ↓
integration test

HTTP / RPC boundary
    ↓
contract test

complete user workflow
    ↓
E2E test

曾经发生过的 bug
    ↓
regression test
```

这里最值得养成的习惯其实非常简单：

> **每修一个 bug，都问：“什么 automated check 可以保证这个 bug 永远不会再次悄悄回来？”**

例如有人发现：

```text
2026-02-29 被日期解析器错误接受
```

不要：

```text
修代码
commit
```

而应该：

```text
1. 写出 reproducing test
2. 确认 test 失败
3. 修复
4. 确认 test 通过
5. 保留这个 test
```

这就是 regression suite 的来源。

长期下来，你的软件历史会逐渐沉淀成一套：

> “我们曾经学到的所有教训的 executable memory”。

这是自动化测试最大的复利。

---

# 六、接下来理解 Eval

如果让我给 Eval 一个数学化的定义，我会写：

\[
Eval = Dataset + Harness + Grader + Metric
\]

分别来看。

### Dataset

你拿什么任务测？

例如做一个邮件摘要 Agent：

```text
普通邮件
超长邮件
多语言邮件
带附件邮件
垃圾邮件
需要行动的邮件
模糊请求
恶意 prompt injection
```

这组 case 实际上隐含着你对：

> “用户世界是什么样的”

的假设。

这比 grader 还重要。

因为：

> 一个系统只能在你的 eval distribution 上表现优秀。

如果 eval 里完全没有中文：

```text
English eval: 98%
```

几乎不能证明：

```text
Chinese users: 98%
```

所以 eval engineering 的核心技能之一实际上是：

**dataset design。**

---

### Harness

如何把系统放进一个可重复环境执行？

例如 Agent 测试可能需要：

```text
临时 filesystem
sandbox
mock email inbox
fake CRM database
browser
tools
network
seed data
```

每次测试结束必须 reset。

否则：

```text
trial #2
```

可能读到了：

```text
trial #1
```

留下来的文件。

这样你的结果就不可信了。

Anthropic 特别强调 agent eval 要使用稳定、隔离的环境，因为共享状态会制造虚假的成功或者相关性失败。:chatgpt-content-reference{index="4"}

---

### Grader

怎么判断成功？

这是 eval 和传统 test 最大的区别之一。

最可靠的 grader 永远优先考虑 deterministic check。

例如要求 AI：

```text
创建 contacts.csv
```

不要问另一个 LLM：

> “这个 agent 好像有没有创建 csv？”

直接：

```python
assert Path("contacts.csv").exists()
```

更好。

要求数据库有记录：

```sql
SELECT ...
```

直接查。

要求 JSON：

```python
jsonschema.validate(...)
```

要求代码正确：

```text
pytest
npm test
go test
```

只有很难 deterministic 判断的时候，才考虑：

```text
LLM grader
human grader
```

例如：

```text
回答是否清晰？
总结有没有抓住重点？
语气是否合适？
```

OpenAI 当前 Evals API 也支持 string checks、text similarity、model graders 以及组合 grader，这正体现了这种混合式思路。:chatgpt-content-reference{index="5"}

---

# 七、为什么 AI Eval 比 Unit Test 难很多

假设：

```python
assert add(1, 2) == 3
```

跑 1000 次：

```text
1000 / 1000
```

但 Agent 做任务：

```text
“分析这个 repo 并修掉登录 bug”
```

可能：

```text
run 1  success
run 2  success
run 3  fail
run 4  success
run 5  fail
```

所以你测的不再只是：

\[
f(x)=y
\]

而是某种：

\[
P(success \mid task, system)
\]

于是 eval 会自然引入统计问题。

例如：

```text
baseline

73 / 100 succeed
```

修改 prompt：

```text
candidate

79 / 100 succeed
```

这时候不能马上宣布：

```text
+6% improvement!
```

因为可能只是 sampling noise。

以后深入学习时，你会逐渐碰到：

```text
variance
confidence interval
statistical significance
sample size
false positive
false negative
inter-rater agreement
grader calibration
```

这就是为什么 Eval Engineering 同时涉及：

```text
software testing
+
experimental design
+
statistics
+
product judgment
```

---

# 八、TDD 和 EDD 的关系

可以用这一张表建立长期 mental model：

| | TDD | Eval-Driven Development |
|---|---|---|
| 驱动力 | failing test | failing / low-scoring eval |
| Specification | test case | eval dataset + rubric |
| 判断 | 通常 deterministic | deterministic + probabilistic |
| 典型对象 | function / class / service | LLM / agent / AI product |
| 输出 | 通常稳定 | 可能随机 |
| 目标 | correctness | capability + quality + reliability |
| 循环 | Red → Green → Refactor | Eval → Diagnose → Improve → Eval |
| regression | tests | regression eval suite |

因此你可以把 EDD 理解成：

```text
TDD mental model
+
experimental methodology
+
non-deterministic systems
```

但不要简单认为：

> EDD = “AI 时代的新 TDD，所以 TDD 没用了”。

恰恰相反。

一个 AI Agent 项目通常同时需要：

```text
普通代码
    → unit tests

database/tools
    → integration tests

agent workflow
    → E2E tests

behavior quality
    → evals
```

Anthropic 甚至给出了一个很有用的区分：**capability eval** 问“它现在能做到什么程度？”，而 **regression eval** 问“以前会的东西现在有没有退化？”；前者应当留下提升空间，后者通常希望接近 100% 通过。:chatgpt-content-reference{index="6"}

---

# 九、拿一个具体 side-project 来看

假设你开发一个：

```text
AI Bookmark Manager
```

用户保存网页，然后系统：

```text
抓取网页
→ 提取正文
→ AI 总结
→ AI 分类
→ AI 打标签
→ 存数据库
```

以前可能是：

```text
写完
↓
打开浏览器
↓
保存几个网页
↓
感觉不错
↓
deploy
```

这就是典型：

> vibe-driven development。

更成熟的做法是：

```text
URL normalize
URL deduplication
HTML parsing
database logic
```

用 unit tests。

比如：

```python
def test_removes_tracking_params():
    assert normalize(
        "https://foo.com/a?utm_source=x"
    ) == "https://foo.com/a"
```

然后：

```text
网页抓取
database repository
external API
```

用 integration tests。

然后最关键的 AI 功能：

```text
summary quality
classification
tagging
```

建立 eval dataset。

比如一条：

```json
{
  "article": "...",
  "expected_category": "machine-learning",
  "must_mention": [
    "transformer",
    "attention"
  ],
  "must_not_claim": [
    "paper uses RNN"
  ]
}
```

grader 可以组合成：

```text
category exact match        20%
required facts              30%
hallucination check         30%
summary quality LLM grader  20%
```

最后再建立几个真正的 E2E case：

```text
given URL
↓
system fetches article
↓
generates summary
↓
creates tags
↓
persists bookmark
↓
UI displays it
```

现在你的项目第一次真正拥有：

> quality system。

---

# 十、Eval-Driven Development 的完整循环

如果把 EDD 写成一个工程循环，我会推荐你长期记住：

```text
Define success
      ↓
Collect representative tasks
      ↓
Build graders
      ↓
Run baseline
      ↓
Inspect failures
      ↓
Classify failure modes
      ↓
Improve system
      ↓
Run eval again
      ↓
Promote solved cases to regression suite
      ↓
Collect new production failures
      └─────────────────────↺
```

这里最容易遗漏的一步是：

> inspect failures。

很多人只看：

```text
score = 82.4
```

实际上 eval 最有价值的输出往往不是 score，而是：

```text
这 17 个 failure 为什么失败？
```

然后形成 taxonomy：

```text
7 tool-selection errors
4 hallucinations
3 context failures
2 bad retries
1 grader bug
```

这时候你才知道该改：

```text
prompt?
model?
tool schema?
retrieval?
architecture?
grader?
```

Anthropic 也非常强调阅读 transcripts：你必须检查失败究竟来自 agent，还是 eval 本身写坏了。:chatgpt-content-reference{index="7"}

---

# 十一、还有一个很重要的概念：Eval 本身也可能有 bug

这是传统测试里已经存在、AI eval 里更加严重的问题。

例如 rubric：

```text
回答必须简洁。
```

什么叫简洁？

20 个字？

200 个字？

一个 grader 认为：

```text
PASS
```

另一个认为：

```text
FAIL
```

那么你的 eval 根本没有可靠 measurement。

因此好的 eval case 应该尽量满足：

> 两个有能力的人独立判断时，应该基本能够得到同样的结论。

这也是为什么 reference solution 很重要。

先确保：

```text
一个你确信正确的答案
```

真的能：

```text
pass graders
```

否则不是系统失败，而可能是 test 失败。

---

# 十二、如果你从 side-project 开始，不要一下进入“测试宗教”

很容易从：

```text
完全不测试
```

突然走到：

```text
我要 100% coverage
我要 mock 一切
我要写 500 个 tests
我要搭一套 enterprise eval platform
```

然后发现：

```text
开发效率降低 70%
```

最后放弃。

更健康的目标是：

> 每一层增加“刚好足够便宜”的反馈。

一个很好的 side-project 初始状态其实只是：

```text
lint + typecheck

20~50 个重要 unit tests

5~10 个 integration tests

2~5 条 critical E2E paths

如果有 AI：
20~50 个真实 eval cases

CI 自动运行
```

值得注意的是，Anthropic 目前给刚开始做 agent eval 的建议也不是“先收集几千条”，而是从大约 20–50 个来自真实行为和失败模式的简单任务开始。:chatgpt-content-reference{index="8"}

这对于个人项目尤其合适。

---

# 十三、我建议你的系统学习顺序

不要先学：

```text
pytest API
Jest API
Playwright API
OpenAI Evals API
某个 eval framework
```

这些都是工具。

先学四层思想：

```text
第一层
Software Testing Fundamentals

↓
什么值得测试
test oracle
test isolation
test doubles
unit / integration / E2E
regression
coverage
property-based testing


第二层
TDD

↓
test list
Red → Green → Refactor
behavior-oriented testing
design for testability
refactoring safely


第三层
Evaluation

↓
dataset
task distribution
grader
rubric
reference answer
metrics
variance
human calibration


第四层
Eval-Driven Development

↓
capability eval
regression eval
failure taxonomy
eval harness
CI
production feedback
continuous eval
```

这比从某个 framework 开始有效得多。

---

# 十四、一个实际可执行的四周学习方案

第一周只学习传统 testing。

选一个你最熟悉的语言，用它自己的主流 testing framework。找一个已有 side-project，不新建玩具项目。给最重要的 domain logic 加 unit tests，然后给数据库/API 加几个 integration tests。

目标不是 coverage，而是你开始能够判断：

```text
这个行为应该在哪一层测试？
```

第二周专门练 TDD。

每天选一个很小的 feature，坚持：

```text
test list
→ Red
→ Green
→ Refactor
```

这一周 Kent Beck 的《Test Driven Development: By Example》非常适合。Martin Fowler 那篇 TDD 简介也非常适合作为入口。:chatgpt-content-reference{index="9"}

第三周进入 Eval。

挑你项目里的一个 AI 功能。

建立：

```text
20~50 cases
```

先不要上复杂框架。

甚至：

```text
evals/
  cases.jsonl
  run.py
  grade.py
```

就够了。

每次运行生成：

```text
pass rate
failure cases
latency
token usage
cost
```

你会比单纯学习某个 Eval SDK 理解得深得多。

第四周把整个体系连接起来：

```text
git push
    ↓
lint
typecheck
unit
integration
    ↓
small regression eval
    ↓
merge
```

重大版本或者模型升级，再运行：

```text
full eval suite
```

这时你已经从：

> “会写测试”

进入：

> “会设计一个验证系统”。

---

# 十五、最终希望形成的开发直觉

以后每写一个功能，脑中应该自然出现五个问题：

```text
What does success mean?

How would I know it works?

What could break?

How can I reproduce that automatically?

How will I know six months later that I didn't regress?
```

这五个问题其实横跨了：

```text
testing
TDD
evaluation
observability
software quality
```

而这也是 AI-assisted coding 越来越强以后，一个非常关键的能力变化：

以前 bottleneck 很大程度上是：

> “我能不能把代码写出来？”

现在代码越来越便宜。

真正稀缺的逐渐变成：

> “我能不能精确定义什么叫正确，并建立一个足够可信的系统持续验证它？”

这正是 TDD 与 Eval-Driven Development 今天重新变得如此重要的共同原因。

如果把整个主题最终压缩成一句话，我建议记：

> **Tests 把 correctness 变成 executable specification；evals 把 quality 变成 measurable specification。**

而一个成熟的软件开发流程，两者都需要。