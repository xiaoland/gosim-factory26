# 主侧补读记录

主Agent已完整消费 visible.txt [0,1240000)。PR14两个单元及PR12 eba7完整；Issue4 ebc5余段交m3，ebdc交m1_m2。1170000:1210000输出中r52截断已整条补齐。

PR14 的正向反例：r119/120 的 subagent_wait 实际等到 bg001 终态（34秒，1 provider finished）；r130/131 对 bg002 等到终态（5m4s）。因此不能由根 ec38 的无active结果推论所有PBB未注册或wait总不工作。
PR14 实际9bedf84：pnpm e2e34/34、干净archive平台路径34/34及PLATFORM_EXIT=0，后端76/76。r126先rm再mkdir archive，有明确干净副本证据，与根第四次PR13 overlay旧目录不同。
PR14 r42 head截掉目标#80，r44认识到thread全量排序导致目标不在head，r45 awk定位补读#80并刷新packet，是自行纠错的正向例子。

## PR14 第二会话补充（133记录全部完成）
06:59 reset 后无需求/head/base 变化仍重跑 Vitest76 + E2E34，耗78.745s。随后背景结果到达后写调用在07:01:30起反复被拒；r93同native session状态idle，r103带WAL只读副本显示正确binding仍idle，r105原turn completed。原Agent自己确认绑定不同种类，不构成绑定错误。r106长篇宿主探索后最终未篡改状态；07:13新notice触发可写轮次，r109成功#101。应核实是否既有完成后扩展续轮问题，不直接定性新bug。r116冻结补充comment反引号发生命令替换，r117报command not found；r122使用body-file修正#102并读回。无需新增shell拦截层。
PR14首会话subagent_wait实际等待34s及5m4s，两次均有终态，限制了root PBB等待异常的外推。

PR12 eba7目前读至r107：r60/r63对reset password多错误契约产生自行例外（错误code/未知邮箱只回code，其他错误不返回），理由把未知邮箱与错误码响应一致视为不能联合password错误；需看后续最终是否保留和契约是否裁决，不立即定性。r88初轮backend48PASS。r94 bg001启动05:42:20.969，r98错误用subagent_wait(id=bg001)立即返回指导，r100通过pbb拿到真实失败：15PASS1FAIL，tail管道exit0但e2e明确exit1。r102原始DOM与URL证明登出到了公共首页，r103修改测试顺序（访问settings/password→login→刷新login→back）后继续，未改应用迁就断言。该测试依然未真正重放原settings/profile历史页面，最终需结合后续补测判断。

PR12 eba7全部141记录已读完。r111平台路径直接在已有pnpm node_modules工作树运行，不符合其脚本注释clean copy前提，60.34s16PASS仅证明该路径；后续根独立验收另查。r123 sleep90轮询生成bg003，r125 all-wait57.1s正例实际等待bg003，平台bg002此前05:45:31已完成；两者不混同。r136/138/140迟到completion逐个造成无新事实final，未重跑。D2自行单错误例外后来已由a194fee修复，af2d06d advisor固化；见下一单元ebc5 r9Git事实，不能列最终缺陷。下一单元ebc5属于Issue4 M2，不是PR12。
