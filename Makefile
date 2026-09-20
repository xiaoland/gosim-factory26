PYTHON ?= python3

.PHONY: bootstrap test run
bootstrap:
	$(PYTHON) scripts/factory.py bootstrap

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) scripts/factory.py run
