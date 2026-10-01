# Exp Console shadcn/ui 迁移回执

2026-10-01。用户直接要求使用shadcn/ui替换Ant Design，并允许调整相关UI/UX。沿用Console直接应用、部署与限定commit授权。

## 结果

前端删除Ant Design及其图标、provider、样式，使用官方生成的16个本地shadcn/ui组件、Radix、Tailwind CSS 4、Lucide和Sonner。组件源码在`braid-console/web/src/components/ui/`，CLI配置在`components.json`，主题在`src/theme.css`；业务组合不提供Ant API兼容层。App/Home继续持有登记与导航，BraidRun/Sessions持有Braid详情；HTTP、后端、归档接入与对象事务未改。

首页增加已登记、现场、归档及写入许可概览，运行卡片突出工作项入口，保存范围和来源按需展开。工作项用Tabs切换类型，搜索可单独清除，全部筛选及空结果可一键重置。导航和工作项列表保持可见，归档说明收为可展开提示。

会话目录增加全部/历史切换和身份、profile、状态搜索。Provider页面先显示原生对话与工具调用，将身份/材料和Turn历史收为折叠区域；Turn每页50条、展开才渲染。原文仍按稳定字节游标读取，不为UI一次加载完整日志。写入按钮明确请求态，编辑预览和确认弹窗使用shadcn组件，保留原revision、草稿与错误处理。

## 实际反馈

TypeScript与Vite生产构建通过：CSS63.41 kB（gzip12.50），首页JS454.70 kB（gzip141.41），进入运行按需加载Braid详情213.76 kB（gzip64.34）。没有大chunk警告；没有编写或运行设施测试。

Chrome实际读取两份登记归档：首页、GitHub Issue #1、PR #2、状态/搜索筛选、Braid agent与provider深链。PR #2会话目录6条、历史5条；Turn共822条、17页，实际切换第2页。Pi原文首页24条记录、字节游标1070367/2644706，页面显示用户、Agent、工具调用/结果和原始记录。返回首页、浏览器后退恢复provider身份、前进返回首页以及首页刷新均可用。实际操作发现的重复React key已修正并重新构建、冻结；最终provider浏览器warning/error为空。

最终服务10条GET保留原始响应：9条HTTP200，包括首页、登记、两份对象/会话目录、Issue/PR及Pi原文；缺native manifest的GitHub原文返回HTTP400，并保留“native manifest 未提供此会话的唯一正文映射；不会回退原工作树或容器”。Pi正文该次GET用时4.945秒；此前20秒读取超时未修改后端，本轮仅确认随后成功读取。归档文件前后12个身份/存在记录一致。

原始证据在`runs/braid-console-control/20261001-shadcn-ui/`：`frontend-build.log`、`http.final.json`、`archive-files.before.json`/`archive-files.after.json`、`navigation.final.json`、`home.final.png`、`provider.final.png`及实际页面文本。没有模型运行、归档修改或业务POST。

## 此批部署（已退役）

后续正式路径路由制品已接替此服务；以下身份保留历史证据，不能用于当前启动。当前入口与制品归[路径路由回执](path-routing.md)。

入口 http://127.0.0.1:8765/。稳定根`/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-shadcn-ui-final`，service ID `97a16025-2f26-4032-b54e-98269264e8fd`，2026-10-01T03:27:45Z启动，HTTP PID38698/PPID1。`service.py show`核对冻结程序、前端和Python身份成功。归档接入仍为`pi-archive-20260920`和`github-final-20260930`，均只读。

前序home PID84660与迁移中间制品PID36159均停止，原权威manifest退役；配置、active和launch保留在新根history，并接续原history。旧journal不存在如实记录。中间服务初次10秒退出期限到达，随后确认active.finished、PID消失并取得服务锁后才退役，没有强制终止或并行启动。新服务没有SSH转发、自启或生成控制操作。

部署原始回执为`prepared-service.final.json`、`service.final.json`、`launch.final.json`、`retirement.final.json`、`process.final.txt`；限定改动提交到父仓库，不push，其它工作区改动保留。

## 未验边界

当前没有live可写现场，不声称草稿确认、真实保存/评论或暂停/恢复已重新验证；也没有Codex原文材料可验。本轮零登记页面未另启空服务重验。保留这些边界，不启动模型或建立现场补验；后续取得对应授权及真实材料后实际操作。
