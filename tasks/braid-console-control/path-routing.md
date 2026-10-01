# Exp Console 正式路径路由回执

2026-10-01。用户明确“我本质上只是想把路由理顺”，并撤销旧参数兼容/跳转：“不用保留现有参数的兼容和跳转”。用户授权开工并要求由subagent实现；保留Python后端，不迁移Node。本轮由子Agent完成实现与部署，主Agent独立复核并沿用项目明确的自主git commit授权限定提交，不push。

## 行为与边界

React Router 7接管显式路由和浏览器history。路径为`/`、`/runs/:run`、`/runs/:run/issues/:id`或`prs/:id`、追加`/agents/:agent`、再追加`/providers/:provider`。页面身份只由路径匹配，旧query身份不再解析或重定向；根路径带旧query仍显示Home，地址不变。搜索/筛选继续页面本地状态，不扩大成筛选持久化。

App作为持久工作区继续持有草稿与busy状态，叶路由提供页面身份而不重新挂载App。Router blocker处理点击和前后导航：busy阻止切换；草稿取消保持原页面，确认丢弃才继续；beforeunload保留。原工作项revision、动作和数据查询语义不变，仍用原Braid接口。

Python对严格合法的应用路径结构返回前端入口，支持深链直接打开和刷新。非法编号、缺层级、未知页面、缺失assets及未知API保留HTTP404具体响应；不把任意404吞成SPA。符合路径结构但未登记运行由前端明确提示，缺失对象和会话保留实际接口错误。用户未要求SSR或后端重写。

权威使用说明更新于Console及web README、部署说明。本回执记录本轮授权、实际反馈及部署身份，历史shadcn回执保留当时结果并标记部署退役。

## 实际反馈

Python编译、TypeScript及Vite构建通过。新增React Router后首页JS546.34kB（gzip171.62），Vite提示超过500kB；Braid详情213.76kB（gzip64.34）、CSS63.41kB（gzip12.50）。没有为消除提示扩大优化范围，没有编写/运行设施测试。

真实两份登记归档HTTP共18条GET：11条200（首页、run、Issue/PR、agent/provider、旧query根页和原数据API），7条404（零编号、超安全整数编号、缺层级、未知路径、assets及API）。保存响应体和状态，旧query无HTTP重定向。未知资源保留JSON错误，不返回入口HTML。

Chrome实际从Home进入Pi Issue、agent、provider；provider显示原生标题与已加载24条记录、字节1070367/2644706。浏览器后退agent、前进provider，以及最终provider/Home之间后退/前进正常；直接provider路径及重载由真实页面核对。GitHub PR #2直接路径展示4条评论，agent目录6个provider链接，provider路径刷新正常。旧query根页显示Home、不显示工作项且不改变地址。

独立主Agent发现中间制品的叶路由未声明element/Component所致React Router warning。已为每个身份叶路由声明显式空视图，保持App生命周期，重新构建冻结最终制品；新Chrome最终页面warning/error为空。原始中间反馈和制品保留，不用旧日志冒充最终。

归档前后12项材料身份/存在记录一致；SQLite WAL/SHM只比较既有存在边界。没有业务POST、Docker控制、模型或建立live现场。当前两archive只读，可写草稿确认、提交和busy期间控制不声称实际重验；保留实现保护和前序边界。

证据在`runs/braid-console-control/20261001-path-routing/`：`build.final.log`、`http.final.json`及各原始body、`navigation.final.json`、`reload.final.json`、`old-query.json`、`browser.logs.final.json`、归档前后材料记录、最终Home/provider截图。主Agent独立baseline和最终证据另以`primary-`前缀保存。最终独立复核包括HTTP边界、PID/PPID与冻结身份，以及新Chrome中的24条正文记录和空warning/error。主Agent另实际重载provider路径、返回首页和浏览器前后导航，均恢复正确页面；旧query根页仍保持原地址并显示Home，证据为`primary-navigation.final.json`和`primary-old-query.final.json`。

## 当前部署

入口 http://127.0.0.1:8765/。新稳定根`/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-path-routing-final`，service ID`4db9c009-e8d5-421b-97ec-b4e1e70c0705`，HTTP PID56220/PPID1，冻结程序、前端和Python校验通过。两份原archive登记保持，不配置自启或SSH。

原shadcn服务PID38698和中间路径制品PID53063均已核对身份、SIGTERM结束并取得服务锁后退役权威manifest。每次新根保存旧manifest、active、launch和既有history；journal未存在如实记录。旧根保留retired-service.json，不删除历史归档/制品。最终只有新manifest表达当前恢复配置。

部署回执为`prepared.final.json`、`retirement.final.json`、`launch.final.json`、`service.final.json`、`process.final.txt`。提交只纳入本轮Console及相关文档，其它工作区改动保留，不push。可写现场的未验边界保留，范围内实现及部署已收尾。
