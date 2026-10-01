PYTHON ?= python3
VARIANT ?= pi-braid
RUNTIME ?=
OUTPUT ?=
RUN ?=
BRAID ?= sources/braid/target/debug/braid
BRAID_RUN_ID ?=

.PHONY: tools package braid-report help
# Tool preparation deliberately does not resolve a variant or install a benchmark.
tools:
	$(PYTHON) scripts/runtime.py prepare

package:
	@test -n "$(OUTPUT)" || (echo '需要 OUTPUT=/path/to/agent.zip'; exit 2)
	$(PYTHON) scripts/package_agent.py --variant "$(VARIANT)" --output "$(OUTPUT)" $(if $(RUNTIME),--runtime "$(RUNTIME)",$(if $(DOCKER_CONTEXT),--docker-context "$(DOCKER_CONTEXT)"))

braid-report:
	@test -n "$(RUN)" -a -n "$(OUTPUT)" || (echo '需要 RUN=/path/to/experiment-run OUTPUT=/path/to/new-site'; exit 2)
	$(PYTHON) -m lab.analysis.braid_telemetry_viewer "$(RUN)" --output "$(OUTPUT)" --braid "$(BRAID)" $(if $(BRAID_RUN_ID),--braid-run-id "$(BRAID_RUN_ID)")

help:
	@echo 'tools         准备原生工具'
	@echo 'package       打包：VARIANT=... OUTPUT=... [RUNTIME=...]'
	@echo 'braid-report  从实验 OTLP Backend 生成诊断网站：RUN=... OUTPUT=... [BRAID=...] [BRAID_RUN_ID=...]'
	@echo '诊断与排障：docs/deployment/braid-diagnostics.md'
