# Braid / GitHub CLI 行为复核

用户要求从参数、行为到help尽可能一致，先分别整理再比较。用户已明确授权“CLI-01~05都可以应用”；当前进入实施，06/07保留产品边界。

目标：降低Agent凭GitHub经验使用Braid时的误用与意外副作用，保留明确的本地多Agent和可编辑上下文能力。
范围：issue/pr创建、查看、列表、修改、评论、关闭/重开、ready/merge；assignee、正文/file/stdin、JSON、错误与help；Braid额外thread/hide/resolve独立标记。

- GitHub独立清单：Sheet审查会话01a0ec30-e24e-7d62-8863-bc2128035b74，只读本机gh和官方手册/源码，输出github.md。
- Braid独立清单：i11_readable_cli，只读当前CLI和实现、必要既有审计副本，输出braid.md。
- 主线取得两份后比较，输出comparison.md。区分可兼容缺陷、明确产品扩展、平台无对应能力、证据不足；不以不同就判错。

不做外部写操作，不创建测试/模拟探针，不把help宣称当实现已证。最终返回高影响差异、根因与修复取舍供用户复核。

## 结果

两份独立清单均完成；主线比较见[comparison.md](comparison.md)。新增CLI-01～07已区分优先兼容缺口与需保留/复核的产品差异；CLI-01～05已获开工授权，由i11_readable_cli负责Braid源码、帮助和内部消费者，主线核对外围消费者及整合；编译和实际只读操作验证，不部署I10。08/10既有修正保留。

## 外围消费者核对

已搜索当前I11 variant、harness、scripts、lab：未发现依赖默认全量list或必填close reason的直接调用；lab/analysis/trace.py读取原始状态里的head_ref/base_ref，故保留既有原始字段，不迁移成仅CLI的公开别名。旧variant与冻结I10包不修改。

CLI-01～05已完成源码和编译/只读操作核对，见[implementation.md](implementation.md)。主线补查宿主state调用并迁移telemetry export。未部署I10；写入行为改善由后续真实运行验证。
