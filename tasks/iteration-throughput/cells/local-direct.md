# Cell：复用冻结包和官方测试的本地对照

production local-simulation镜像缺失只阻断复刻该环境，不阻断本地官方测试。采用同一已冻结Agent ZIP，在WSL CPython3.12直接执行标准main.py入口，再把已交付应用交给现有factory.evaluate及固定官方ARC测试。结果标为local-cpython-arcbench，不宣称官网或production local-simulation成绩。

入口为../scripts/local-package-run.py。生成和评测的证据目录分开；评测输入仅覆盖task、deployment=arcbench和固定benchmark revision，不改生成原始记录。已有delivered应用恢复时直接复用，保留此前评测日志。没有新增评分实现或隔离。

WSL现已准备：Python3.12.14、应用评测使用Node20.19.3；官方arc-bench revision 1eb018367bedd618d3b9ced406ce07fb423d4956且工作树干净；既有Playwright/Chromium复用。包内Pi使用自己固定的Node24，不依赖宿主Node。三个待对照ZIP已复制至runs/packages/iteration-throughput-boundary/。脚本--help和py_compile通过。2026-09-23已在WSL并行启动DeepSeek/Keep与GLM/BookStack，首次持久状态均为generating；具体证据见`runs/local/iteration-throughput-boundary/`，未把它们称为官网成绩。

是否提前启动两路本地对照、与官网mixed并行，已向用户明确询问；这改变此前“先mixed两题闭环、再其余variant”的顺序。未收到确认前不启动新本地生成，官网既有任务继续运行。
