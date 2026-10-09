# 业务状态转移的验收

先从原始需求明确前态、动作、可见成功或失败终态，再选择下一动作。登录按钮的tap完成只证明执行了点击；URL改变也可能早于页面完成。HTTP200能帮助诊断请求，但不能代替所要求的页面或账户状态。客户端校验可以不发请求，不强制每一步都有HTTP屏障。

使用当前冻结版本`e2e guide writing-tests`中的完整示例、fixture解构和API；不要凭其它浏览器库的API记忆写检查。每个用例从自己的页面/会话前态开始。数据库是否重置由场景前态决定，不要求每case新建数据库；每个验收执行仍隔离服务、数据和浏览器身份。

## 有期限的可见终态

为状态转移选择局部、明确的等待预算，记录来源：需求规定的性能约束优先，否则说明当前环境的验收预算。不要改全局timeout/retries、固定sleep、全局network-idle或重复非幂等提交以“解决”失败。功能结果与响应耗时分别报告；放宽预算后通过不能证明原先的慢操作没有问题。

下例演示一个完整的成功登录检查。示例的账号、可见消息及20秒局部预算必须按允许需求和本次环境替换，20秒不是Harness默认值。等待成功或失败终态后，再断言需求要求的成功页面；可见拒绝会让第二个断言失败并留证，不会被当成完成通过。

```ts
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('valid account reaches its workspace', async ({ app, screen }) => {
  const transitionBudgetMs = 20_000; // 此用例说明来源，不修改全局预算。
  await app.open('/');
  await screen.getByRole('link', 'Sign in').tap();
  await screen.getByLabel('Username or email').fill('example-user');
  await screen.getByLabel('Password').fill('Example-password-123!');
  await screen.getByRole('button', 'Sign in').tap();
  await expect(screen.getByText(/^(Welcome, example-user|Invalid credentials)$/))
    .toBeVisible({ timeout: transitionBudgetMs });
  await expect(screen.getByRole('heading', 'Welcome, example-user')).toBeVisible();
  // 后续依赖认证状态的动作只能放在成功页面断言之后。
});
```

负向检查应要求准确错误消息及未变状态，不把任何错误都当预期拒绝。登出要证明未认证态，然后再后退或直开受保护页；保存要证明可见保存结果，再刷新核对持久状态。依赖前态的流程不要靠“重新打开链接”替换需求明确要求的reload、back或其它动作。

## 首次失败与有区分力的复测

首次失败保留独立output目录、真实退出值、候选、用例/步骤、URL、可见状态、trace及截图。对提交中超时，定向核对同一次动作的请求是否发出、响应状态与耗时、页面断言采样窗口及后续状态：未发请求可能是编排或客户端校验；拒绝响应或成功后页面仍不符合要求优先调查应用；只有原始证据否定工具完成声明或证明观测能力故障时才归工具设施。

复测前记录测试源码/config、等待预算、服务版本、数据初态、会话、场景序列、并行负载和cache是否变化。修改已有应用时，数据初态应指向受验收业务基线的独立副本；删除数据库后重新播种只构成空库初始化观察，不能称为同条件升级复测。不要求为调查复制所有数据，但不得把条件不同的复测称为同条件验证。单场景重复通过可以补强功能证据，不能冲销全量旅程中的首次失败；保留原失败、后续通过及尚未排除的时延/状态风险。需要证明原缺陷消失时，恢复原必要前置并独立执行该旅程。报告未经证明的责任归因，不凭disabled截图断言是CPU、代理或业务错误。
