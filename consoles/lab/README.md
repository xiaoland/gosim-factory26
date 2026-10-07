# Factory26 Lab Console

当前 run 的只读页面和保存状态由 `python3 -m lab serve --config FILE` 提供；本目录只包含 Lab Console 的 React/Vite 前端。后端入口在 [lab/serve.py](../../lab/serve.py)，页面主体在 [RunOverview.tsx](web/src/RunOverview.tsx)，接入合同见[Console 运行说明](../../docs/deployment/console.md)。

在仓库根目录安装共享依赖并构建 Lab 前端：

```sh
pnpm --dir consoles install --frozen-lockfile
pnpm --dir consoles build:lab
```

构建输出 `web/dist/` 由 Lab service 的 `static_root` 配置消费。Braid 协作对象、讨论、会话和旧冻结服务的独立前端与 Python 入口归 [consoles/braid](../braid/README.md)，不在本目录复制或冻结。

成功保存后，生产者发布 workspace 的文件清单和保存回执中的实际目录。清单最多500个文件，排除 `.git`、`node_modules`、`.factory26`，明确显示截断和读取错误，不上传文件内容。Console 可以定位文件，但暂不提供内容预览或下载；保存路径属于回执所在宿主，不能当作 Console 服务器路径。日志面板同样只展示末尾65,536字节，并给出完整原件的保存位置。原生 session state 是最近保存事实，不能替代 run 的执行 lifecycle。
