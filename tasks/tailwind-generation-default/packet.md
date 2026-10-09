# 现行生成指令统一 Tailwind CSS

## 当前决定与授权

用户明确要求“统一替换为tailwindCSS”，授权本轮修改现行 Harness 的生成指令。负责人为 i14_combo_sequential_owner；只修改样式默认及必要验收条件，不改协作职责、业务应用、模型或执行设施。不得提交或推送。

新建应用统一使用 Tailwind CSS；接续既有应用保持基线技术栈和数据语义，不要求已生成的决赛应用迁移。指令按实际选择的版本要求官方构建集成与 CSS 导入、应用入口加载确认，以及正式构建页面的代表性计算样式验收。动态样式使用版本适配的完整类名映射或 CSS 变量，不继续混用 UnoCSS/safelist 表述。

## 实际范围

- `variants/pi-braid-i13/run.py`
- `variants/pi-braid-i13-glm-root/run.py`
- `variants/pi-braid-i14/run.py`
- `variants/pi-braid-i14-cleaner/run.py`
- `variants/pi-braid-i14-reviewer/run.py`
- `variants/pi-braid-i14-reviewer-direct/run.py`
- `variants/pi-braid-i14-cleaner-direct/run.py`
- `variants/pi-braid-i14-e2e/run.py`
- `variants/pi-braid-i14-reviewer-cleaner-e2e/run.py`
- `variants/pi-braid-flash-team/run.py`
- `variants/I14-dx-test/run.py`
- `variants/pi-braid-kimi-root/run.py`
- `variants/pi-braid-coordinator/run.py`
- `variants/pi-braid-review/run.py`
- `variants/pi-minimal/instructions.md`
- `variants/pi-minimal-vv-dx-test/instructions.md`
- `variants/pi-minimal-vv/instructions.md`
- `CONTRIBUTING.md`

三个独立对照 pi-braid-kimi-root/coordinator/review 原无 RUN_CONDITIONS，通过其既有 user_instructions 接线新增局部 UI_CONDITIONS；不增加共享模板。Pi minimal-vv 保留既有应用技术栈及数据保护要求，新增新建应用默认。

依据 variants/README.md，排除 I10 pi-braid、I11、I12、历史 pi-team 系列及归档停用实现。Console 已使用 Tailwind CSS，无需修改。旧 runs、冻结 ZIP 和在途应用未修改。共享工作区原有 dirty 改动保留。

## 检查与交付

本轮已由主线采用并完成；14 个 run.py、3 份 Pi 指令和 CONTRIBUTING.md 共 18 个文件已更新。packet 自身为新增记录。未启动或控制任何运行，未提交或推送。

已完成 14 个 run.py 的 Python AST 语法、RUN_CONDITIONS/UI_CONDITIONS 实际常量及 native_files 消费接线读取；3 个 Pi instructions.md 的 Tailwind 默认、CSS 导入、入口加载、计算样式和动态类约束读取检查通过。现行范围无 UnoCSS/safelist 指令残留，窄 diff 核对通过。此轮不运行 Factory/Braid 测试、模型生成或制品 smoke；这些检查只证明指令已进入现行源码，不能宣称已有应用样式已修复。官方版本依据为 https://tailwindcss.com/docs/installation/using-vite，指令保持版本中性，不硬锁 v4。

主线收敛：Braid 的 Tailwind 构建集成与导入要求仅在采用 Tailwind CSS 时适用，避免强迫既有应用迁移；正式构建页面的计算样式验收仍为通用要求。14 个 run.py 窄修后 AST 读取通过。
