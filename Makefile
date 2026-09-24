PYTHON ?= python3
VARIANT ?= pi-team-mixed
RUNTIME ?=
OUTPUT ?=
DOCKER_CONTEXT ?= arcbox-win

.PHONY: tools package
# Tool preparation deliberately does not resolve a variant or install a benchmark.
tools:
	$(PYTHON) scripts/runtime.py prepare

package:
	@test -n "$(OUTPUT)" || (echo '需要 OUTPUT=/path/to/agent.zip'; exit 2)
	$(PYTHON) scripts/package_agent.py --variant "$(VARIANT)" --output "$(OUTPUT)" $(if $(RUNTIME),--runtime "$(RUNTIME)",--docker-context "$(DOCKER_CONTEXT)")
