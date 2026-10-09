# 实验 AI 模型提供商

本页是提供商选型入口。价格、套餐限制与验证来源按供应商维护，可执行的端点和模型映射由[原生LiteLLM配置](../../materials/model-gateway.json)集中管理，密钥位于私有env。核对日期为2026-10-03（Asia/Shanghai）。

选型不使用Kimi K2.7 Code HighSpeed或DeepSeek V4.1 Flash（原厂别名deepseek-flash）；普通K2.7 Code及其它供应商的V4 Flash 0731保留。同名模型不保证同一版本。账户余额、价格有效期及具体模型权限在新实验准备时核实。

| 提供商 | 选型与价格 | 已有验证边界 |
| --- | --- | --- |
| Moonshot Kimi | [K3与K2.7 Code](model-providers/kimi.md) | 2026-10-07两精确模型ID目录200；自费配方已加入官方备用，未额外验证Chat。 |
| BigModel 智谱 | [GLM-5.3与Flash](model-providers/bigmodel.md) | Flash历史短文本成功。 |
| DeepSeek原厂 | [保留凭据与历史证据](model-providers/deepseek.md) | 原厂Flash已转接V4.1，当前排除；其它模型未选定。 |
| 千问 | [普通API与Token Plan](model-providers/qwen.md) | 两通道目录核对；普通Flash短文本成功，不等于完整Pi验收。 |
| 方舟Ark Coding Plan | [Flash、Kimi与订阅套餐](model-providers/ark.md) | 通道配置已维护；所选配方和实际调用从对应实验输入及 run 核对，不沿用旧接入阶段状态。 |
| 共绩算力MaaS | [普通备选](model-providers/gongji.md) | 凭据已填，实际调用待验证。 |
| Command Code GOAT | [Flash与订阅套餐](model-providers/command-code.md) | 凭据尚未填，实际调用待验证。 |
| 百度千帆 | [普通API与个人Token Plan](model-providers/qianfan.md) | 两套凭据均已填；两通道GLM-5.3请求ID已核实，实际调用待验证。 |
| MiniMax 官方 | [M3与按量价格](model-providers/minimax.md) | 官方请求ID及中国区端点已核实；key待填写，实际调用待验证。 |
| ARC Benchmark | [冻结模型与额度边界](model-providers/arc.md) | 有历史运行及定向调用证据，版本结论保留限制。 |

按量价格统一列每100万tokens（M），区分未缓存输入、输出、缓存读取和写入；人民币与美元保留原币种。套餐价格和token计量价分别记录，不将LiteLLM估算费用当成实际账单。千帆活动价使用元/千tokens发布，换算到元/M需乘1000。

本目录描述可选供应商及其事实，不持有本次角色模型或回退顺序。已选有序路由从[跨 variant 模型配方](../../materials/model-recipes/README.md)进入，通过现有 --route/--gateway-routes 输入装配；catalog 的默认条目不能替代已选配方。网关运行绑定见[Lab](../../lab/README.md)，材料装配见[打包说明](../../tooling/scripts/README.md)，接续见[恢复说明](recovery.md)。运行冻结实际消费配置，客户端保留稳定模型名；供应商切换不改在途实例。授权归所属 packet，配置存在不构成模型调用或恢复许可。

持续事实更新对应供应商页，实际调用原件保留在run及[接入packet](../../tasks/external-model-providers/packet.md)。本页不维护另一份可执行路由表。
