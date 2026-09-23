PYTHON ?= python3

.PHONY: bootstrap run
bootstrap:
	$(PYTHON) scripts/factory.py bootstrap

run:
	$(PYTHON) scripts/factory.py run
