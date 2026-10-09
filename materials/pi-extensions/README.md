# 维护中的 Pi 扩展

本目录持有 pi-minimal-vv 与 pi-braid-i15-reviewer-cleaner-e2e 的自实现扩展源码。Exa 与 Pi timing 两个共享实现各保留一份；宿主专属的 capability evidence、owned E2E、Braid cleaner 与 subagent observer 保留独立行为。第三方扩展仍由 materials/npm 的锁与补丁生产，此目录不复制第三方代码。

选择与实际复制由 tooling/scripts/pi_extensions.py 维护。variant 入口只引用交付的 extensions/ 文件；vv build、公共组件生产与 I15 冻结 overlay 使用相同源映射，并将源文件与选择器身份纳入回执或缓存依赖。交付复制真实文件，不通过 symlink 或另一个 variant 的 import 寻源。owned-e2e.ts 仍位于交付 extensions/，相对引用 ../tools/owned-e2e.mjs 不变。

修改扩展时更新本目录；不要在 variant 内恢复副本。历史冻结包与尚未迁移的历史 variants 保持原身份，不因维护目录变化自动更新。
