# I11 独立 variant

2026-09-29 用户要求复制 I10 为新 variant，在当前实验继续时开发 I11。
已复制 `variants/pi-braid/` → `variants/pi-braid-i11/`（不含Python缓存），仅改运行身份为pi-braid-i11；入口、角色、扩展、工具和build保持独立文件。
共用打包器的OTLP材料选择已加入新名字，否则新variant会漏打包既有观测依赖。

Braid/SVC仍在sources独立仓库维护，技能通过harness/skills链接装载；没有复制第三方依赖树或重建配置生成器。
I10使用已冻结ZIP 7d8dc70a…与已记录hotfix二进制继续；不得从当前SVC/Braid源码重新生成I10包。当前Sheet热修复负责人继续按独立快照构建。
I11将从新variant及明确的Braid/SVC修订构建，制品记录实际来源。尚未构建或启动新实验，当前variant文件复制本身不证明行为改善。

直接核对复制差异及Python语法，不运行Harness测试或模型。未来I11改动只改新variant；共同Braid修复要明确是否向I10热部署，不能隐式改变运行输入。
