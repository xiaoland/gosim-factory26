# T02 | turn f5b54180-45f0-4bdb-ace5-d2d88fcf7cea | startedAt 1787720832.903589


## userMessage | message f5b54180-45f0-4bdb-ace5-d2d88fcf7cea


你说的这些，似乎都没什么问题，不少东西我也知道。但是，似乎没有满足我的需求。一方面你给了很长一段的回复；另一方面，你似乎把agent eval和我想要知道的软件工程里面的自动化测试、eval给混杂在一起了。

## agentMessage | message 85751cc6-f195-49e4-a33f-1d1ddf0fc7d4


是的。前一条真正的问题不是细节错误，而是“课程边界”没有划清楚。

还有一个术语上的原因需要说明：我刚刚重新核对了一下，2026 年大家谈的 “Eval-Driven Development / EDD”，目前这个词的主流公开用法确实主要针对 AI-assisted、LLM 或其他 probabilistic software，而不是传统软件工程中一套与 TDD 并列的成熟理论。:chatgpt-content-reference{index="0"} 所以我把 EDD 引向 Agent Eval 并非完全无关，但对于你想补的知识来说，确实喧宾夺主了。

我建议我们把学习对象重新定义成三个彼此分开的东西：

1. **Software Testing / Quality Engineering**
   
   这是主干，也是你真正缺少系统经验的地方。研究的是“如何系统地发现软件缺陷、证明某些性质成立，以及如何建立自动化反馈体系”。

   这里应该系统学习：
   `fault / error / failure → test oracle → test case design → unit / integration / system / acceptance test → test doubles → coverage → property-based testing → fuzzing → mutation testing → regression → CI → flaky tests → performance / reliability testing`。

2. **Test-Driven Development**
   
   这是“怎么利用测试来驱动开发和设计”的方法论，而不是“软件测试理论”的同义词。

   重点应该深入到 Red-Green-Refactor 之外，例如 test list、triangulation、testability、Classical vs Mockist TDD、outside-in vs inside-out，以及测试如何影响 API 和模块边界。

3. **Evaluation / Measurement**
   
   先不用把它理解成 Agent Eval。一般软件工程里，我们也经常要回答一些不是单个 `assert` 能回答的问题：
   
   “新版到底有没有更好？”  
   “性能退化了多少？”  
   “搜索算法 A 和 B 哪个质量更高？”  
   “压缩算法在一个数据集上的表现如何？”  
   “系统是否达到 release threshold？”
   
   这里对应的是 **benchmark、metrics、experiments、quality gates、acceptance criteria、regression measurement** 等思想。它与 testing 有交集，但不是一回事。

最简单的区别是：

```text
Testing:
对于这个 case，系统是否满足某个性质？
→ pass / fail

Evaluation:
在一组 workloads / scenarios / metrics 上，
这个系统表现得怎么样？
→ measurement / distribution / score / comparison
```

例如数据库：

```text
自动化测试：
插入失败时 transaction 是否 rollback？
→ assert database_state == expected_state
```

而 evaluation：

```text
在 10GB workload 上：
Postgres 配置 A vs B

p50 latency
p99 latency
throughput
CPU
memory
```

后者完全没有 LLM，也依然是 evaluation。

所以如果重新给你安排学习路线，我不会再从 Agent Eval 开始，而会这样走：

```text
I. 软件测试的理论基础
        ↓
II. 自动化测试的方法与测试架构
        ↓
III. TDD：测试如何驱动设计
        ↓
IV. 高级测试方法
    property / fuzz / mutation / contract / E2E
        ↓
V. 软件 Evaluation
    benchmark / metric / experiment / quality gate
        ↓
VI. 最后才讨论：
    AI 时代这些思想为什么又变重要
```

而且我建议我们**慢下来，一次讨论一个主题**，不要再一次塞一整本书。

下一步最适合从一个非常基础、但其实很深的问题开始：

> **“一个 automated test 究竟是什么？一个好的 test 到底提供了什么证据？”**

从这个问题出发，可以自然推导出 test oracle、test case、SUT、fixture、unit/integration、mock、coverage 等整套概念。这个基础打牢之后再进入 TDD，会比从 pytest/Jest 或 Red-Green-Refactor 开始系统得多。