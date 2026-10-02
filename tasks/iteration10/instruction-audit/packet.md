# Instruction 审查

本子任务只读核对上一轮 `e20260928-02-deepseek-direct` 两题冻结材料与迭代 10 当前待打包源码。目标是从 Braid 成员和原生子角色实际消费的输入层识别矛盾、冗余、边界混淆及接线缺失；不把角色文件存在视为已注入，不把技能目录等同已读正文。

授权仅含调查及本目录材料整理。禁止源码、Corpus、提示词、冻结应用、原始记录修改；不运行 benchmark、模型、Factory/Corpus 测试，不提交。采用 ponytail lite，建议只定位最小权威所有者，不应用修正。

调查顺序：装配入口与生成材料 → 角色有效输入矩阵 → 独立发现 → 与 review/closure 对账。远端证据根和 SHA-256 记录于 sources.json；报告中的旧版生效与当前源码推断分别标记。

## 已完成覆盖与判断

已读取当前 variant/run.py、Braid provider/context 装配、两题 312 个 Braid 会话输入索引、1,610 份 native-home 角色文件版本、65 条 subagent/subagent_wait 工具反馈，以及旧冻结末态和当前预热镜像的 Pi/subagents/PBB 指令相关源码。原生 skill 元数据与 SOP 正文分别核对。已先保存 independent-findings，再对账 review/closure。

实质发现：运行共同约束在根 prompt 的 user 层，未稳定进入独立 Braid 子项或 fresh 子角色；当前整合段给 PR 与根负责人两个根关闭主语。旧 vision dispatch guard 误拒已被当前 completionGuard:false 修正；另有 acceptance 推断为实现/reviewer 的语义偏离，但进一步核对发现 review-required 是 non-blocking，不能据 meta 声称阻止完成/返回。本项已从冻结前高优先级缺口降为非阻断观察。

交付 report.md、input-matrix.md、session-matrix.md、native-role-matrix.md、sources.json、excerpts.md 及只读采集脚本。后续主线负责实施；本子任务没有源码修改、测试、模型运行或提交。

## 可直接交给主线的最小实施切口

1. `variants/pi-braid/run.py` 定义短的运行共同约束文本：本次 origin 的修改范围、无人中途介入、禁止外部评测材料、平台启动/兼容/保留目录契约、端口/数据/进程隔离。`native_files` 将它注入两个 profile 的 user_instructions 和有 bash 的四个原生角色 append body；vision 已仅允许读取委派给定材料，可保持原契约。当前只做 BACKGROUND_COMPLETION_RULE 的拼接位置可就近复用，不新增模板框架。根 prompt 原运行约束段改为引用/保留根自身必要目标，避免同个根 session 同文两份；平台部署契约仍应让负责实现的成员能取得。保留子任务原需求、局部授权、接口、反馈由父提供，不全量继承历史。
2. 两个 `agents/*/instructions.md:9` 只删整合 PR 负责人句中的「关闭根 Issue」，保留末尾根负责人判断完整交付后关闭规则。两处按同一文字修改，暂不为两个 profile 去重新增模块。
3. 不因 review-required 字段新建 reviewer 或给所有原生角色加一轮验收。保持当前 false guard；账本解释两层差别。是否消除自动 acceptance 的错误角色语义，以真实父消费影响或明确产品决定为依据。

实施后允许的核对是静态装配比对：检查生成路径实际追加的文本及两 profile/四角色覆盖，确认 vision 无多余可写工具/继承、旧运行材料未变。不得新建或运行 Factory/Corpus 测试；真实采用交由已授权后续两题实验。
