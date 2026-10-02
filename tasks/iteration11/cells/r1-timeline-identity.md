# R1：协作时间线的对象身份

当前状态：用户批准“按此修正”后，已完成源码修正、编译与归档副本实际只读核对；未部署、未恢复实验。

## 问题与修正

GitHub I10 中 Agent 将时间线内部活动序号 #89 当作评论 ID，实际目标为 Comment 32。上一版加“活动序号 + 来源评论”虽可区分，却把内部映射变成使用者负担，已替换。

Issue/PR 共用 print_timeline 现在直接呈现 Comment ID、作者、动作与读取入口。非评论活动只呈现参与者、动作及对象/事实。文本不逐行展示活动序号或时间；只有页尾续读命令携带分页游标。移除共用 instruction 中解释双编号的提示。数据库 source_comment 关联、查询顺序、分页与结构化 JSON 保持原状，它们仍可用于程序诊断。

--timeline 是 Braid 历史读取扩展；gh issue view 原生提供 --comments，没有该参数。此次对齐协作对象语义，不宣称命令完全兼容。

## 实际核对

cargo build 成功（有 dead_code 警告）。对既有归档数据库副本 /tmp/braid-r1-readonly.63qBhn 运行：

```text
braid --state TEMP issue view 1 --timeline --after 85 --limit 8

协作历史：8 条；后面还有记录。
@glm-1 edited title/body changed
@glm-1 edited title/body changed
Comment 43 · @deepseek-5 · commented
  braid comment view 43
Comment 45 · @glm-1 · replied
  braid comment view 45
@glm-1 edited title/body changed
Comment 48 · @Braid · commented
  root progress check
  braid comment view 48
@glm-1 edited title/body changed
@glm-1 linked_pr PR #14
下一页：braid issue view 1 --timeline --after 166 --limit 8（每页最多 100 条）
```

评论动作重复的 detail（comment #ID）省略，其余事实与原因保留。没有新增测试或探针，未提交。该证据确认读取呈现，模型实际使用效果留待获授权实验。
