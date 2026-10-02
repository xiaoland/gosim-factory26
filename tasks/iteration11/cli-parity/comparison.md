# CLI 对照：优先消除已有 GitHub 经验的误用点

两份清单已分别完成，再做本对照：[GitHub CLI 2.89.0](github.md)、[当前 Braid](braid.md)。依据是本机help、固定版本官方源码及Braid实现；没有做外部写入或模拟测试。本页是审查与待复核建议，不是新功能已实施声明。

## 目标与判断标准

Agent应能用已有GitHub CLI经验完成本地协作，不必先学习内部数据结构。优先比较同名命令/参数是否表达同一意图、默认查询是否让用户看到预期集合、输出是否能作为后续命令输入、错误是否给出准确下一步。
保留用户已确认的产品差异：指派工作创建独立成员、单负责人和独立工作区；thread/hide/resolve是上下文管理能力。本地没有GitHub远端账户或网页，不伪造URL、权限或异步合并队列。对齐不是复制所有gh功能或其偶然实现细节。

## 值得优先修复的兼容缺口

| 编号 | GitHub CLI行为 | Braid当前行为 | 影响及建议 |
| --- | --- | --- | --- |
| CLI-01 关闭语义 | issue close无需reason；可选reason是completed/not planned/duplicate，解释文字用comment；pr close没有reason，二者有comment入口 | Issue/PR close都强制任意字符串reason，无comment参数；merged PR close的错误却写cannot reopen | 熟悉gh的裸close失败，reason同名不同意。建议issue reason可选且采用明确状态原因；自由文字通过comment，PR移除强制reason。补close/reopen的comment入口，帮助和状态回执说明真实变更；历史自由理由不能冒充枚举值，历史数据保留。实现前明确旧reason兼容取舍 |
| CLI-02 列表默认与筛选 | 默认open、limit30、创建时间倒序，状态/assignee/base/head等常用筛选；PR closed包括closed和merged | 所有状态、编号升序、无状态筛选/limit | 随运行变长，旧完成项遮挡当前工作。建议优先补state/limit/assignee及PR base/head，默认open、最新在前；同步现有调用者需要全量时显式all。无需直接实现GitHub Search语法/远程分页 |
| CLI-03 JSON字段语义 | number是可操作编号，id是不透明远端ID；PR字段headRefName/baseRefName/isDraft等；--json需字段，--jq可选 | 可操作编号叫id，分支字段head_ref/base_ref，draft；--json可裸用；无jq/template | 直接套用gh的--json number,headRefName会失败。建议支持相应公开字段名，以number为操作编号；不为模仿gh而向LLM暴露UUID。旧字段兼容与裸json是扩展，可明示。jq/template是否必要另算，不借此引入整个格式化框架 |
| CLI-04 常用参数/评论操作 | create支持-a，view -c，list -L/-s；comment --edit-last/--delete-last；同一用户已有经验可复用 | 多个长参数没有对应短写；只能comment edit ID/delete ID操作具体评论 | 建议低成本短别名优先；edit-last/delete-last若纳入要明确定义“当前Braid成员最后一条评论”。保留精确comment ID与thread扩展，不增加不存在于gh的comment create别名来迎合误用 |
| CLI-05 合并入口与结果 | --merge/--squash/--rebase；普通非交互缺策略会报错；还可能auto/queue；match-head原样送expectedHeadOid | 只支持本地merge提交，直接merge执行，输出merge_commit JSON；--merge也不识别 | 至少让--merge落到已有实现，并说明当前只有即时本地merge；未实现的squash/rebase/auto/queue不可静默接受。是否改变已有不带策略入口默认，需与运行指令一并决定。保留精确head匹配，不为了看起来灵活放松 |

上述来源逐项可由两份清单的命令段和官方固定版本链接定位。最优先是01/02/03：它们改变用户对状态、当前工作集合和对象身份的理解；短别名等次之。

## 需要产品选择的差异

### CLI-06 PR创建不是同一工作方式

gh默认以当前Git分支为head，base取显式参数/gh-merge-base/默认分支，不要求关联Issue，流程可能push或fork。
Braid必须--issue，省略head会从base建独立PR分支，再由PR负责人实施；默认base为调用方delivery ref。
这承载既有“先设计Issue、再交PR实现”的产品模型，不能在CLI清理中偷换成“代码写完才创建PR”。
建议先保留显式--head支持和Braid既有新PR工作区流程，在help明确默认来源、已发布分支条件、--issue关联不等于关闭；是否允许无关联Issue PR、是否按调用方当前分支猜head，作为单独产品决定复核。
不移植gh可能push的--dry-run；Braid未实现此参数，不能补一个名字却产生意外写入。

### CLI-07 指派身份是已确认的扩展

gh增加/移除已有登录用户的assignee集合；Braid通过可重复的指派名称产生独立成员，每项只有一个负责人，改派需remove当前成员+add选择名称。
这是用户已确认的能力，不应为了兼容变为添加成员、复用原生session或多负责人。I11-02已改善入口/回执，仍需真实运行确认理解效果。
help应明确此差异，并拒绝尚未有一致含义的@me、逗号多名，而不是假装兼容。

## 应保留或暂不扩展

- comment thread/reply-to、hide理由、resolve折叠、reaction，以及直接指定评论阅读是Braid额外能力；不能因gh顶层没有这些命令而删除。
- Braid同一run中按整数定位工作项、共享Issue/PR编号序列保留；gh支持网页URL和当前Git分支，Braid无网页不能伪造URL。若支持当前分支推断，必须无歧义且对错误明确，不把它作为本轮必需修复。
- gh仅view/list有JSON；Braid创建回执、ready/merge的JSON对Agent有用，不应为形式一致移除。区分同名字段语义兼容与有意增加的结构化返回。
- gh create的body-file覆盖body、comment edit-last与delete-last某组合优先delete，是版本实现细节；不建议复制这种输入歧义。Braid互斥校验更明确，help说明即可。
- TTY交互、editor/web、远端认证、fork、merge queue、reviewer/label/project完整系统暂不因本次审查扩展。无人值守入口用明确参数，不引入交互等待。
- 不要求Braid复刻gh副作用的非事务失败：例如评论已发但close失败、push成功但create失败。Braid应报告实际状态，不能把失败概括成“没有修改”。

## 已一致或本轮已经修正

正文编辑替换完整内容，-F读取文件、-F -读取stdin、缺文件报错；未指定正文的edit保留旧正文。I11-10已把这一点落实到帮助与准备文件后的写入流程。
PR ready/--undo为草稿切换，不代表验收或合并；merged PR不能重新打开。Braid关闭关键词仅在默认分支合入时关闭Issue，背景link不等于关闭意图。
空列表可成功，参数或业务失败有非零退出及具体stderr；Braid的解析失败码不完全等于gh的用户取消码，但本地无交互取消语义，不建议只为数字统一吞掉原始错误。

## 建议实施顺序与验证

先复核01/02/03的明确参数/字段/默认值方案，再实现04的高频参数别名和05的--merge入口。06/07保持现有产品边界，若用户另作决定再变更。
核对每个改变的既有命令消费者，尤其list默认过滤、JSON字段和close reason；迁移实际调用指令，不靠新help覆盖旧示例。
按仓库要求不加CLI测试/探针，使用编译、真实只读操作和已授权运行轨迹验证；不得在正在进行的I10上试写对象。新源码进入I11包前记录版本，行为改善由后续运行验证。
