## 整合 PR #13 已验收合并 — 交付完成（受检提交 develop@eec19cf → main@c3fb22d）

**整合验收中发现并修复一处需求级种子偏差（bb9bbe6）**：requirements.yaml 全文以 `acme-docs`（291 处）为中央种子仓库，而实现把分支 main/feature-search、`Document search flow` 提交、`src/search.ts`、种子 issues/PRs 全放在了 `web-app`（内部命名，需求中出现 0 次），官方按需求场景验收会直接失败。已对齐：`acme/acme-docs` 承载全部中央种子；补 `documentation` 标签与 `Q3 launch` 里程碑（Improve onboarding）、Legacy welcome text 补 bug 标签、新增 Open PR `Improve onboarding`（bob-reviewer，保持 Fix search 为 alice 唯一 Open PR 以满足 REQ-6-2-1 作者过滤）、acme 组织补 REQ-2-2-3 团队层级种子；顺带修复团队授权按名称全局解析导致跨组织重名 team 误授的潜在缺陷（限定仓库所属组织）。e2e 脚本同步对齐（eec19cf）。明细见 PR #13 comment 87。

**最终候选 eec19cf 验收证据（glm-13 执行；临时 DATA_DIR、非 3000 端口、自启服务已停止、各套件独立端口）**
1. 构建链（全新顺序）：frontend `npm install && npm run build` ✓（dist/index.html sha256 `6fce146b…`）→ backend `npm install && npm test` **73/73 PASS**。
2. 启动验收：`HOST=0.0.0.0 PORT=3946 DATA_DIR=<tmp> npm run start`，**3 秒内**首页 200（≤120s 预算）；better-sqlite3 原生模块本次安装即正常，无需 rebuild。
3. 全量 e2e 复跑：req1 **72/72**（3941）、req4 **24/24**（3942）、req6a **89/89**（3943）、req6b **103/103**（3944）、req3 **19/19**（3945）——已按 comment 75 要求使用互不相同的独立端口。
4. 种子逐项核实（API 断言 32 项全过）：alice-dev/bob-reviewer/carol-maintain/dave-admin/eve-reader（`Valid-password-123!`，bob 登录实测 200）、acme 组织（含 platform-team→frontend-team→frontend-child）、acme/acme-docs main+feature-search、`src/search.ts`、README 含 "search flow"、issues `Improve onboarding`（open，bug+documentation，Q3 launch，assignee bob-reviewer，1 评论）/`Legacy welcome text`（closed，bug）/`Original issue title`、PR `Fix search`（open，feature-search→main，**3 additions / 1 deletions**，src/search.ts modified + main-only.md added）、PR `Improve onboarding`（open，bob-reviewer）、closed `Update welcome copy`（alice-dev）、draft `Draft onboarding update`、`Prepare release notes` 带 pending check `test`、`acme/merge-demo`（Merge ready/Merge blocked）、`acme/protect-demo`（public，无预置规则）、issue/PR 共享编号连续（issues 1,2,8；PRs 3–7，next_number=9）。

**编号说明**：新增种子 PR 后共享计数器 next_number 由 8 变 9（需求只要求仓库内唯一递增；PR 正文旧清单的 "next_number=8" 是旧种子状态的描述，已随正文更新说明）。

PR #13 已以 `--match-head-commit eec19cf` 合并，origin/main 现为 **c3fb22d**（Merge local PR #13）。PR 正文中的验收清单各项均已在最终候选上执行并满足，请据此判断完整交付并关闭根 Issue。
